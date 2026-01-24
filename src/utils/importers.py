"""Nubank CSV importers for credit card and checking account statements."""

import csv
import io
import logging
import re
from base64 import b64decode
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Auto-categorization mapping for common keywords
AUTO_CATEGORIES = {
    "Transferência": "Transferência Interna",
    "Resgate": "Transferência Interna",
    "Rendimento": "Investimentos",
    "Pagamento de fatura": "Transferência Interna",
    "Pagamento recebido": "Transferência Interna",
}


def _extract_installment_info(description: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract installment information from transaction description.

    Looks for patterns like "01/10", "1/12", "03-06" indicating
    installment numbers (e.g., "3rd of 6 installments").

    Validates that current <= total to avoid false positives (e.g., dates like "10/12").

    Args:
        description: Transaction description string.

    Returns:
        Tuple of (current_installment, total_installments) or (None, None) if not found.

    Example:
        >>> _extract_installment_info("Loja X 01/10")
        (1, 10)
        >>> _extract_installment_info("Normal transaction")
        (None, None)
    """
    if not description:
        return None, None

    # Pattern: digits, separator (/ or -), digits
    # Example: "01/10", "1-12", "03/06"
    pattern = r"(\d{1,2})[/-](\d{1,2})"
    matches = re.findall(pattern, description)

    if not matches:
        return None, None

    # Use the last match (usually most relevant)
    current_str, total_str = matches[-1]
    current = int(current_str)
    total = int(total_str)

    # Validate: current should be <= total (to avoid false positives like dates)
    if current <= total and current > 0:
        logger.debug(f"Detectada parcela: {current}/{total} em '{description}'")
        return current, total

    return None, None


def clean_header(header_list: List[str]) -> List[str]:
    """Normalize CSV headers for comparison.

    Converts all headers to lowercase and removes whitespace.

    Args:
        header_list: List of header strings from CSV.

    Returns:
        List of normalized (lowercase, stripped) headers.

    Example:
        >>> clean_header(["Data", " Valor ", "Descrição"])
        ['data', 'valor', 'descrição']
    """
    return [h.strip().lower() for h in header_list]


def parse_upload_content(
    contents: str,
    filename: str,
    classification_history: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Parse Nubank CSV upload and normalize to standard format.

    Detects whether the CSV is from a credit card or checking account
    and applies appropriate date format and sign logic.

    Args:
        contents: Base64-encoded CSV file content.
        filename: Original filename (for logging).

    Returns:
        List of standardized transaction dictionaries with keys:
            - data (str): ISO format date (YYYY-MM-DD)
            - descricao (str): Transaction description
            - valor (float): Absolute value (always positive)
            - tipo (str): "receita" or "despesa"
            - categoria (str): Default "A Classificar"

    Raises:
        ValueError: If CSV format cannot be detected or parsing fails.

    Example:
        >>> transactions = parse_upload_content(base64_content, "file.csv")
        >>> transactions[0]
        {
            'data': '2025-01-15',
            'descricao': 'Padaria do João',
            'valor': 45.50,
            'tipo': 'despesa',
            'categoria': 'A Classificar'
        }
    """
    try:
        # Decode base64 to string
        decoded = b64decode(contents).decode("utf-8")
        csv_file = io.StringIO(decoded)

        # Read CSV with DictReader
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError("CSV vazio ou inválido")

        # Normalize headers for detection
        normalized_headers = clean_header(reader.fieldnames)

        # Detect format
        is_credit_card = _is_credit_card_format(
            normalized_headers,
        )
        is_checking_account = _is_checking_account_format(
            normalized_headers,
        )

        if not is_credit_card and not is_checking_account:
            logger.error(
                f"Formato CSV desconhecido em {filename}. "
                f"Headers: {reader.fieldnames}",
            )
            raise ValueError(
                "Formato de CSV não reconhecido. "
                "Use extratos do Nubank (Cartão ou Conta).",
            )

        # Parse based on format
        if is_credit_card:
            return _parse_credit_card(
                reader,
                normalized_headers,
                classification_history,
            )
        else:
            return _parse_checking_account(
                reader,
                normalized_headers,
                classification_history,
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar CSV {filename}: {str(e)}",
            exc_info=True,
        )
        raise


def _is_credit_card_format(headers: List[str]) -> bool:
    """Check if headers match Nubank credit card format.

    Args:
        headers: Normalized CSV headers.

    Returns:
        True if format matches credit card (has 'title' and
        'amount'), False otherwise.
    """
    return "title" in headers and "amount" in headers


def _is_checking_account_format(headers: List[str]) -> bool:
    """Check if headers match Nubank checking account format.

    Args:
        headers: Normalized CSV headers.

    Returns:
        True if format matches checking account (has 'data' and
        'valor'), False otherwise.
    """
    has_date = "data" in headers
    has_value = "valor" in headers
    has_description = "descrição" in headers or "descricao" in headers
    return has_date and has_value and has_description


def _apply_history(
    row: Dict[str, Any],
    history: Optional[Dict[str, Dict[str, Any]]],
) -> None:
    """Apply classification history to suggest category and tags.

    Uses intelligent substring matching to find similar past transactions.
    Prioritizes historical classifications when no category is assigned.

    Args:
        row: Transaction row dict with 'descricao', 'categoria', 'tags' keys.
        history: Classification history dict from get_classification_history().

    Returns:
        None (modifies row in-place).
    """
    if not history or not isinstance(history, dict):
        return

    # Normalize current description
    descricao_atual = row.get("descricao", "").lower().strip()
    if not descricao_atual:
        return

    # Search for intelligent match in history
    for descricao_historica, classificacao in history.items():
        # Bidirectional substring matching:
        # - Check if historical description is in current description
        # - OR if current description is in historical description
        if (
            descricao_historica in descricao_atual
            or descricao_atual in descricao_historica
        ):

            # Extract historical values
            hist_categoria = classificacao.get("categoria", "A Classificar")
            hist_tags = classificacao.get("tags", "")

            # Fill category if empty
            categoria_aplicada = False
            if not row.get("categoria") or row["categoria"] == "A Classificar":
                row["categoria"] = hist_categoria
                categoria_aplicada = True

            # Fill tags if empty
            tags_aplicadas = False
            if hist_tags and not row.get("tags"):
                row["tags"] = hist_tags
                tags_aplicadas = True

            # Log detailed information about applied classification
            log_msg = f"Classificação histórica aplicada: '{descricao_atual}'"
            if categoria_aplicada:
                log_msg += f" | Categoria: '{hist_categoria}'"
            if tags_aplicadas:
                log_msg += f" | Tags: '{hist_tags}'"
            if not categoria_aplicada and not tags_aplicadas:
                log_msg += " (sem mudanças aplicáveis)"

            logger.info(log_msg)
            return  # Use first match found


def _parse_credit_card(
    reader: csv.DictReader,
    normalized_headers: List[str],
    classification_history: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Parse credit card statement rows.

    Nubank credit card format:
    - Date format: YYYY-MM-DD
    - Positive values: expenses (despesa)
    - Negative values: credits/refunds (receita)

    Args:
        reader: CSV DictReader object.
        normalized_headers: List of normalized headers.

    Returns:
        List of standardized transaction dictionaries.
    """
    transactions = []
    original_headers = reader.fieldnames or []

    # Find actual header names (case-insensitive)
    date_key = _find_key(original_headers, "date")
    amount_key = _find_key(original_headers, "amount")
    title_key = _find_key(original_headers, "title")

    for row_num, row in enumerate(reader, start=2):
        try:
            data_str = row.get(date_key, "").strip()
            valor_str = row.get(amount_key, "").strip()
            descricao = row.get(title_key, "").strip()

            if not data_str or not valor_str:
                logger.warning(
                    f"Linha {row_num} incompleta. Ignorando.",
                )
                continue

            # Check for payment lines (internal transfers) - mark as disabled, not skipped
            skipped = False
            disable_edit = False
            if descricao.lower().strip().startswith("pagamento recebido"):
                disable_edit = False  # Allow editing to ensure proper categorization
                logger.info(
                    f"Linha {row_num}: Detectado 'pagamento recebido': {descricao}",
                )

            # Parse date (YYYY-MM-DD)
            data_obj = datetime.strptime(
                data_str,
                "%Y-%m-%d",
            )
            data_iso = data_obj.strftime("%Y-%m-%d")

            # Parse value
            valor = float(valor_str.replace(",", "."))

            # Determine type based on sign
            if valor > 0:
                tipo = "despesa"
            elif valor < 0:
                tipo = "receita"
            else:
                logger.warning(
                    f"Linha {row_num}: valor zero ignorado.",
                )
                continue

            # Extract installment information from description
            # Keeps description original, only extracts metadata
            parcela_atual, total_parcelas = _extract_installment_info(descricao)

            # Initialize transaction dict
            transaction = {
                "data": data_iso,
                "descricao": descricao or "Sem descrição",
                "valor": abs(valor),
                "tipo": tipo,
                "categoria": "A Classificar",
                "tags": "",
                "parcela_atual": parcela_atual,
                "total_parcelas": total_parcelas,
                "skipped": skipped,
                "disable_edit": disable_edit,
            }

            # PRIORITY 1: Apply historical classification (if available)
            _apply_history(transaction, classification_history)

            # PRIORITY 2: Auto-categorize based on static keywords
            if transaction["categoria"] == "A Classificar":
                for keyword, cat in AUTO_CATEGORIES.items():
                    if keyword.lower() in descricao.lower():
                        transaction["categoria"] = cat
                        logger.info(
                            f"Linha {row_num}: Auto-categorizada como '{cat}' (palavra-chave: '{keyword}')",
                        )
                        break

            transactions.append(transaction)

        except ValueError as e:
            logger.warning(
                f"Erro ao processar linha {row_num}: {str(e)}",
            )
            continue

    return transactions


def _parse_checking_account(
    reader: csv.DictReader,
    normalized_headers: List[str],
    classification_history: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Parse checking account statement rows.

    Nubank checking account format:
    - Date format: DD/MM/YYYY
    - Negative values: expenses (despesa)
    - Positive values: credits/income (receita)

    Args:
        reader: CSV DictReader object.
        normalized_headers: List of normalized headers.

    Returns:
        List of standardized transaction dictionaries.
    """
    transactions = []
    original_headers = reader.fieldnames or []

    # Find actual header names (case-insensitive)
    date_key = _find_key(original_headers, "data")
    value_key = _find_key(original_headers, "valor")
    description_keys = [
        _find_key(original_headers, "descrição"),
        _find_key(original_headers, "descricao"),
    ]
    description_key = next(k for k in description_keys if k)

    for row_num, row in enumerate(reader, start=2):
        try:
            data_str = row.get(date_key, "").strip()
            valor_str = row.get(value_key, "").strip()
            descricao = row.get(description_key, "").strip()

            if not data_str or not valor_str:
                logger.warning(
                    f"Linha {row_num} incompleta. Ignorando.",
                )
                continue

            # Check for payment lines (internal transfers) - mark as disabled, not skipped
            skipped = False
            disable_edit = False
            if descricao.lower().strip().startswith(
                "pagamento de fatura"
            ) or descricao.lower().strip().startswith("pagamento recebido"):
                skipped = True
                disable_edit = True
                logger.info(
                    f"Linha {row_num}: Marcada como desabilitada (pagamento de fatura): {descricao}",
                )

            # Parse date (DD/MM/YYYY -> ISO)
            data_obj = datetime.strptime(
                data_str,
                "%d/%m/%Y",
            )
            data_iso = data_obj.strftime("%Y-%m-%d")

            # Parse value
            valor = float(valor_str.replace(",", "."))

            # Determine type based on sign (opposite of credit card)
            if valor < 0:
                tipo = "despesa"
            elif valor > 0:
                tipo = "receita"
            else:
                logger.warning(
                    f"Linha {row_num}: valor zero ignorado.",
                )
                continue

            # Extract installment information from description
            # Keeps description original, only extracts metadata
            parcela_atual, total_parcelas = _extract_installment_info(descricao)

            # Initialize transaction dict
            transaction = {
                "data": data_iso,
                "descricao": descricao or "Sem descrição",
                "valor": abs(valor),
                "tipo": tipo,
                "categoria": "A Classificar",
                "tags": "",
                "parcela_atual": parcela_atual,
                "total_parcelas": total_parcelas,
                "skipped": skipped,
                "disable_edit": disable_edit,
            }

            # PRIORITY 1: Apply historical classification (if available)
            _apply_history(transaction, classification_history)

            # PRIORITY 2: Auto-categorize based on static keywords
            if transaction["categoria"] == "A Classificar":
                for keyword, cat in AUTO_CATEGORIES.items():
                    if keyword.lower() in descricao.lower():
                        transaction["categoria"] = cat
                        logger.info(
                            f"Linha {row_num}: Auto-categorizada como '{cat}' (palavra-chave: '{keyword}')",
                        )
                        break

            transactions.append(transaction)

        except ValueError as e:
            logger.warning(
                f"Erro ao processar linha {row_num}: {str(e)}",
            )
            continue

    return transactions


def _find_key(
    headers: List[str],
    target: str,
) -> str:
    """Find the actual key in headers matching normalized target.

    Case-insensitive search for flexibility with different formats.

    Args:
        headers: Original CSV headers.
        target: Normalized target header name.

    Returns:
        The original header key if found, empty string otherwise.

    Example:
        >>> _find_key(["Date", "Amount"], "date")
        'Date'
    """
    target_lower = target.lower().strip()
    for header in headers:
        if header.lower().strip() == target_lower:
            return header
    return ""
