"""零第三方依赖的 XLSX 数据交换与 PDF 报表。"""

from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from PySide6.QtGui import QPageSize, QPdfWriter, QTextDocument

from services.book_service import add_book, list_books
from services.reader_service import add_reader, list_readers
from services.statistics_service import dashboard_counts, popular_books


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26); name = chr(65 + remainder) + name
    return name


def write_xlsx(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    all_rows = [headers] + rows; xml_rows = []
    for row_index, row in enumerate(all_rows, 1):
        cells = []
        for column, value in enumerate(row, 1):
            ref = f"{_column_name(column)}{row_index}"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value or ""))}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>'
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="数据" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def read_xlsx(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(item.itertext()) for item in strings]
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}; result=[]; matrix=[]
    for row in root.findall(".//m:row", ns):
        values=[]
        for cell in row.findall("m:c", ns):
            kind=cell.get("t"); value=""
            if kind=="inlineStr": value="".join(cell.itertext())
            else:
                node=cell.find("m:v",ns); value=node.text if node is not None else ""
                if kind=="s" and value: value=shared[int(value)]
            values.append(value)
        matrix.append(values)
    if not matrix: return []
    headers=matrix[0]
    for row in matrix[1:]: result.append({headers[i]: row[i] if i<len(row) else "" for i in range(len(headers))})
    return result


def export_books(path: Path) -> None:
    headers=["ISBN","书名","作者","出版社","分类","总库存","可借库存","馆藏位置","状态"]
    rows=[[b["isbn"],b["title"],b["author"],b["publisher"] or "",b["category_name"] or "",b["total_count"],b["available_count"],b["location"] or "","正常" if b["status"] else "停用"] for b in list_books(include_inactive=True)]
    write_xlsx(path,headers,rows)


def export_readers(path: Path) -> None:
    headers=["用户名","姓名","电话","状态","创建时间"]
    rows=[[r["username"],r["real_name"],r["phone"] or "","正常" if r["status"] else "停用",r["created_at"]] for r in list_readers(include_inactive=True)]
    write_xlsx(path,headers,rows)


def import_books(path: Path, operator_id: int) -> tuple[int,list[str]]:
    success=0; errors=[]
    for number,row in enumerate(read_xlsx(path),2):
        try: add_book(row.get("ISBN",""),row.get("书名",""),row.get("作者",""),int(float(row.get("总库存","1") or 1)),publisher=row.get("出版社",""),location=row.get("馆藏位置",""),operator_id=operator_id); success+=1
        except (ValueError,TypeError) as exc: errors.append(f"第 {number} 行：{exc}")
    return success,errors


def import_readers(path: Path, operator_id: int, default_password: str="123456") -> tuple[int,list[str]]:
    success=0; errors=[]
    for number,row in enumerate(read_xlsx(path),2):
        try: add_reader(row.get("用户名",""),default_password,row.get("姓名",""),row.get("电话",""),operator_id); success+=1
        except ValueError as exc: errors.append(f"第 {number} 行：{exc}")
    return success,errors


def export_dashboard_pdf(path: Path) -> None:
    counts=dashboard_counts(); books=popular_books(10)
    rows="".join(f"<tr><td>{i}</td><td>{escape(b['title'])}</td><td>{escape(b['author'])}</td><td>{b['loan_count']}</td></tr>" for i,b in enumerate(books,1))
    html=f"""<h1>图书管理系统统计报表</h1><p>图书种类：{counts['book_titles']}　馆藏总量：{counts['total_copies']}　有效读者：{counts['readers']}　当前在借：{counts['borrowed']}　当前逾期：{counts['overdue']}</p><h2>热门图书</h2><table border='1' cellspacing='0' cellpadding='5'><tr><th>排名</th><th>书名</th><th>作者</th><th>借阅次数</th></tr>{rows}</table>"""
    writer=QPdfWriter(str(path)); writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4)); document=QTextDocument(); document.setHtml(html); document.print_(writer)
