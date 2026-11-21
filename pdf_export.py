import os
import sys
from fpdf import FPDF

if getattr(sys, "frozen", False):
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_REGULAR = os.path.join(BUNDLE_DIR, "static", "DejaVuSans.ttf")
FONT_BOLD = os.path.join(BUNDLE_DIR, "static", "DejaVuSans-Bold.ttf")


def generate_tree_pdf(tree_data):
    """Prima dict {'persons': [...], 'partnerships': [...]} i vraća bajtove vektorskog PDF-a."""
    persons = tree_data.get("persons", [])
    partnerships = tree_data.get("partnerships", [])

    # Dimenzije u milimetrima (mm) za vektorski PDF
    card_w = 46.0
    card_h = 18.0
    gap_x = 10.0
    partner_gap = 4.5
    row_h = 42.0
    margin = 20.0

    if not persons:
        pdf = FPDF(unit="mm", format="A4")
        pdf.add_page()
        pdf.add_font("DejaVu", "", FONT_REGULAR)
        pdf.set_font("DejaVu", size=14)
        pdf.cell(0, 10, "Obiteljsko stablo je trenutno prazno.")
        return bytes(pdf.output())

    person_map = {p["id"]: p for p in persons}
    partner_map = {p["id"]: [] for p in persons}
    for pt in partnerships:
        p1, p2 = pt["person1_id"], pt["person2_id"]
        if p1 in partner_map and p2 in partner_map:
            partner_map[p1].append(p2)
            partner_map[p2].append(p1)

    placed = set()
    pos = {}

    def get_unit(p):
        partners = [
            person_map[pid]
            for pid in partner_map.get(p["id"], [])
            if pid in person_map and pid not in placed
        ]
        return [p] + partners

    def measure_unit(p, visited):
        unit = [u for u in get_unit(p) if u["id"] not in visited]
        for u in unit:
            visited.add(u["id"])

        unit_w = len(unit) * card_w + max(0, len(unit) - 1) * partner_gap

        kids = []
        for child in persons:
            if child["id"] in visited:
                continue
            if any(child.get("father_id") == u["id"] or child.get("mother_id") == u["id"] for u in unit):
                kids.append(child)

        kids.sort(key=lambda x: x.get("birth_year") or 9999)

        if not kids:
            return {"unit": unit, "kids": [], "width": unit_w}

        kid_trees = []
        kids_total_w = 0.0
        for k in kids:
            if k["id"] not in visited:
                kt = measure_unit(k, visited)
                kid_trees.append(kt)
                kids_total_w += kt["width"]

        if len(kid_trees) > 1:
            kids_total_w += (len(kid_trees) - 1) * gap_x

        return {
            "unit": unit,
            "kids": kid_trees,
            "width": max(unit_w, kids_total_w),
        }

    def layout_tree(tree, left_x):
        unit = tree["unit"]
        kids = tree["kids"]
        unit_w = len(unit) * card_w + max(0, len(unit) - 1) * partner_gap

        if not kids:
            cx = left_x + (tree["width"] - unit_w) / 2.0
            for u in unit:
                pos[u["id"]] = {"x": cx, "y": u["generation"] * row_h, "person": u}
                placed.add(u["id"])
                cx += card_w + partner_gap
            return

        kids_total_w = sum(kt["width"] for kt in kids) + (len(kids) - 1) * gap_x
        kid_start_x = left_x + (tree["width"] - kids_total_w) / 2.0

        for kt in kids:
            layout_tree(kt, kid_start_x)
            kid_start_x += kt["width"] + gap_x

        first_kid_unit = kids[0]["unit"]
        last_kid_unit = kids[-1]["unit"]
        first_kid_x = pos[first_kid_unit[0]["id"]]["x"]
        last_kid_right_x = pos[last_kid_unit[-1]["id"]]["x"] + card_w
        kids_center_x = (first_kid_x + last_kid_right_x) / 2.0

        parent_start_x = kids_center_x - unit_w / 2.0
        for u in unit:
            pos[u["id"]] = {"x": parent_start_x, "y": u["generation"] * row_h, "person": u}
            placed.add(u["id"])
            parent_start_x += card_w + partner_gap

    roots = sorted(
        [p for p in persons if not p.get("father_id") and not p.get("mother_id")],
        key=lambda x: (x["generation"], x.get("birth_year") or 9999),
    )

    visited_measure = set()
    forest = []
    for r in roots:
        if r["id"] not in visited_measure:
            forest.append(measure_unit(r, visited_measure))

    for p in persons:
        if p["id"] not in visited_measure:
            forest.append(measure_unit(p, visited_measure))

    cur_x = 0.0
    for tree in forest:
        layout_tree(tree, cur_x)
        cur_x += tree["width"] + gap_x * 1.5

    # Izračun točnih granica cijelog stabla za jednu veliku stranicu
    min_x = min(v["x"] for v in pos.values())
    max_x = max(v["x"] + card_w for v in pos.values())
    min_y = min(v["y"] for v in pos.values())
    max_y = max(v["y"] + card_h for v in pos.values())

    header_h = 16.0
    page_w = max(210.0, (max_x - min_x) + margin * 2)
    page_h = max(148.0, (max_y - min_y) + margin * 2 + header_h)

    offset_x = margin - min_x
    offset_y = margin + header_h - min_y

    pdf = FPDF(unit="mm", format=(page_w, page_h))
    pdf.set_auto_page_break(False)
    pdf.add_page()

    pdf.add_font("DejaVu", "", FONT_REGULAR)
    pdf.add_font("DejaVu", "B", FONT_BOLD)

    # Naslov na vrhu dokumenta
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(margin, margin - 6)
    pdf.cell(0, 10, f"Obiteljsko stablo (ukupno osoba: {len(persons)})")

    # 1. Linije partnerstva (narančasta)
    pdf.set_draw_color(217, 119, 6)
    pdf.set_line_width(0.6)
    for pt in partnerships:
        a = pos.get(pt["person1_id"])
        b = pos.get(pt["person2_id"])
        if a and b:
            pdf.line(
                a["x"] + offset_x + card_w / 2.0,
                a["y"] + offset_y + card_h / 2.0,
                b["x"] + offset_x + card_w / 2.0,
                b["y"] + offset_y + card_h / 2.0,
            )

    # 2. Linije roditelj -> dijete (siva, bez preklapanja)
    obitelji = {}
    for child in persons:
        if not child.get("father_id") and not child.get("mother_id"):
            continue
        kljuc = f"{child.get('father_id') or 'none'}_{child.get('mother_id') or 'none'}"
        if kljuc not in obitelji:
            obitelji[kljuc] = {
                "father_id": child.get("father_id"),
                "mother_id": child.get("mother_id"),
                "children": [],
            }
        obitelji[kljuc]["children"].append(child)

    pdf.set_draw_color(100, 116, 139)
    pdf.set_line_width(0.4)
    for idx, ob in enumerate(obitelji.values()):
        f_pos = pos.get(ob["father_id"]) if ob["father_id"] else None
        m_pos = pos.get(ob["mother_id"]) if ob["mother_id"] else None
        if not f_pos and not m_pos:
            continue

        if f_pos and m_pos:
            start_x = (f_pos["x"] + m_pos["x"] + card_w) / 2.0 + offset_x
            start_y = f_pos["y"] + card_h / 2.0 + offset_y
        else:
            single = f_pos or m_pos
            start_x = single["x"] + card_w / 2.0 + offset_x
            start_y = single["y"] + card_h + offset_y

        pomak = 6.0 + (idx % 6) * 2.2
        grananje_y = (f_pos or m_pos)["y"] + card_h + offset_y + pomak

        pdf.line(start_x, start_y, start_x, grananje_y)

        sve_x = [start_x]
        for c in ob["children"]:
            if c["id"] in pos:
                sve_x.append(pos[c["id"]]["x"] + card_w / 2.0 + offset_x)
        pdf.line(min(sve_x), grananje_y, max(sve_x), grananje_y)

        for c in ob["children"]:
            c_pos = pos.get(c["id"])
            if c_pos:
                end_x = c_pos["x"] + card_w / 2.0 + offset_x
                pdf.line(end_x, grananje_y, end_x, c_pos["y"] + offset_y)

    # 3. Kartice osoba
    for p in persons:
        p_pos = pos[p["id"]]
        x = p_pos["x"] + offset_x
        y = p_pos["y"] + offset_y
        is_female = p.get("gender") == "F"

        if is_female:
            pdf.set_fill_color(253, 242, 248)
            pdf.set_draw_color(219, 39, 119)
        else:
            pdf.set_fill_color(239, 246, 255)
            pdf.set_draw_color(37, 99, 235)

        pdf.set_line_width(0.45)
        pdf.rect(x, y, card_w, card_h, style="DF")

        # Ime i prezime
        puno_ime = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        pdf.set_font("DejaVu", "B", 8.5)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(x + 1, y + 3.0)
        pdf.cell(card_w - 2, 5.0, puno_ime, align="C")

        # Godine rođenja i smrti
        b_year = p.get("birth_year")
        d_year = p.get("death_year")
        if b_year or d_year:
            godine = f"{b_year or '?'} – {d_year or ''}"
            pdf.set_font("DejaVu", "", 7.5)
            pdf.set_text_color(71, 85, 105)
            pdf.set_xy(x + 1, y + 9.5)
            pdf.cell(card_w - 2, 4.5, godine, align="C")

    return bytes(pdf.output())
