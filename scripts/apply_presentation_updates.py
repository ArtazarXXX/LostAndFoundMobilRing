#!/usr/bin/env python3
"""
apply_presentation_updates.py
Applies all planned presentation updates from docs/PRESENTATION_CHANGES_PLAN.md:
- Replaces GIF animations with the newly recorded GIFs from docs/recordings/
- Updates texts, headings, bold runs, and styling on slides 1, 4, 5, 6, 7, 8, 9, 10, 11, 12
- Configures Slide 10 with the P2P chat animation and properly positioned diagram
"""

import os
import shutil
import xml.etree.ElementTree as ET

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
UNPACKED_DIR = os.path.join(BASE_DIR, "unpacked_presentation")
RECORDINGS_DIR = os.path.join(BASE_DIR, "docs", "recordings")

NAMESPACES = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

def copy_gifs():
    print("--- 1. Copying GIF animations ---")
    media_dir = os.path.join(UNPACKED_DIR, "ppt", "media")
    os.makedirs(media_dir, exist_ok=True)
    
    mapping = {
        "gif_slide5.gif": "image13.gif",
        "gif_slide6.gif": "image15.gif",
        "gif_slide8.gif": "image19.gif",
        "gif_slide9.gif": "image21.gif",
        "gif_slide10.gif": "gif_slide10.gif"
    }
    
    for src_name, dst_name in mapping.items():
        src_path = os.path.join(RECORDINGS_DIR, src_name)
        dst_path = os.path.join(media_dir, dst_name)
        if os.path.exists(src_path):
            shutil.copyfile(src_path, dst_path)
            size_mb = os.path.getsize(dst_path) / (1024 * 1024)
            print(f"Copied {src_name} -> {dst_name} ({size_mb:.2f} MB)")
        else:
            print(f"WARNING: Source {src_path} not found!")

def create_p(runs, algn="l", space_bef=0, space_aft=0, line_spc=120000):
    """
    Creates an <a:p> element with given runs.
    Each run in runs is a dict:
    {
      'text': str,
      'sz': int,
      'b': bool,
      'color': hex_str or None,
      'font': str (default 'Arial')
    }
    """
    p = ET.Element('{http://schemas.openxmlformats.org/drawingml/2006/main}p')
    pPr = ET.SubElement(p, '{http://schemas.openxmlformats.org/drawingml/2006/main}pPr', {
        'marL': '0', 'marR': '0', 'lvl': '0', 'indent': '0', 'algn': algn, 'rtl': '0'
    })
    
    if line_spc:
        lnSpc = ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}lnSpc')
        ET.SubElement(lnSpc, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcPct', {'val': str(line_spc)})
    
    if space_bef > 0:
        spcBef = ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcBef')
        ET.SubElement(spcBef, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcPts', {'val': str(space_bef)})
    else:
        spcBef = ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcBef')
        ET.SubElement(spcBef, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcPts', {'val': '0'})
        
    if space_aft > 0:
        spcAft = ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcAft')
        ET.SubElement(spcAft, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcPts', {'val': str(space_aft)})
    else:
        spcAft = ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcAft')
        ET.SubElement(spcAft, '{http://schemas.openxmlformats.org/drawingml/2006/main}spcPts', {'val': '0'})
        
    ET.SubElement(pPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}buNone')
    
    for r_data in runs:
        r = ET.SubElement(p, '{http://schemas.openxmlformats.org/drawingml/2006/main}r')
        b_val = '1' if r_data.get('b', False) else '0'
        sz_val = str(r_data.get('sz', 2400))
        font_name = r_data.get('font', 'Arial')
        
        rPr = ET.SubElement(r, '{http://schemas.openxmlformats.org/drawingml/2006/main}rPr', {
            'lang': 'ru-RU', 'sz': sz_val, 'b': b_val, 'i': '0', 'u': 'none', 'strike': 'noStrike', 'cap': 'none'
        })
        
        color_val = r_data.get('color')
        if color_val:
            sFill = ET.SubElement(rPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill')
            ET.SubElement(sFill, '{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr', {'val': color_val})
            
        ET.SubElement(rPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}latin', {'typeface': font_name})
        ET.SubElement(rPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}ea', {'typeface': font_name})
        ET.SubElement(rPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}cs', {'typeface': font_name})
        
        t = ET.SubElement(r, '{http://schemas.openxmlformats.org/drawingml/2006/main}t')
        t.text = r_data.get('text', '')
        
    # endParaRPr
    ET.SubElement(p, '{http://schemas.openxmlformats.org/drawingml/2006/main}endParaRPr', {
        'lang': 'ru-RU', 'sz': str(runs[0].get('sz', 2400)) if runs else '2400', 'b': '0'
    })
    return p

def update_tx_body(sp, paragraphs):
    txBody = sp.find('{http://schemas.openxmlformats.org/presentationml/2006/main}txBody')
    if txBody is None:
        return
    # Remove existing <a:p>
    for child in list(txBody):
        if child.tag.endswith('p'):
            txBody.remove(child)
    for p in paragraphs:
        txBody.append(p)

def update_slide1():
    print("--- Updating Slide 1 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide1.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;19;p3':
            # Надзаголовок / Плашка номинации
            p = create_p([
                {'text': 'Хакатон «Мобил-ринг» • Кейс №4 • Номинация: Профи', 'sz': 1800, 'b': True, 'font': 'Calibri', 'color': '1C3354'}
            ], algn='l', line_spc=100000)
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;18;p3':
            # Заголовок и подзаголовок
            p_title = create_p([
                {'text': 'Бюро находок: Поиск и возврат вещей', 'sz': 4600, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=1400, line_spc=110000)
            
            p_sub = create_p([
                {'text': 'Цифровая платформа поиска и безопасной передачи утерянных вещей с защитой от мошенничества и встроенным чатом', 'sz': 2400, 'b': False, 'font': 'Arial', 'color': '333333'}
            ], algn='l', line_spc=120000)
            update_tx_body(sp, [p_title, p_sub])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide4():
    print("--- Updating Slide 4 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide4.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is not None and cNvPr.attrib.get('name') == 'Google Shape;66;p6':
            # Fix typo 'Разработь' -> 'Разработать'
            p = create_p([
                {'text': 'Разработать приложение, обеспечивающее сбор, систематизацию, хранение информации об утерянных вещах для быстрого возврата их владельцам.', 'sz': 2600, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=120000)
            update_tx_body(sp, [p])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide5():
    print("--- Updating Slide 5 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide5.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;79;p7':
            p = create_p([
                {'text': 'Главный экран', 'sz': 4200, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;77;p7':
            p_hdr = create_p([
                {'text': 'Умная навигация и фильтрация', 'sz': 3000, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=1200, line_spc=110000)
            
            p_body = create_p([
                {'text': 'Интерфейс строго разделяет сценарии на «Находки» (что уже нашли) и «Пропажи» (что ищут владельцы). Поиск и разделение по категориям фильтруют ленту на лету. Каждая карточка содержит качественное фото, место, дату и категорию.', 'sz': 2400, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=125000)
            update_tx_body(sp, [p_hdr, p_body])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide6():
    print("--- Updating Slide 6 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide6.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;89;p8':
            p = create_p([
                {'text': 'Публикация объявления', 'sz': 4200, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;87;p8':
            p_hdr = create_p([
                {'text': 'Быстрое оформление за 30 секунд', 'sz': 3000, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=1200, line_spc=110000)
            
            p_body = create_p([
                {'text': 'Пользователь выбирает тип объявления, категорию из списка, указывает аудиторию или локацию и прикрепляет фото.', 'sz': 2400, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=125000)
            update_tx_body(sp, [p_hdr, p_body])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide7():
    print("--- Updating Slide 7 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide7.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;89;p8':
            p = create_p([
                {'text': 'Административная веб-панель модерации', 'sz': 4200, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;87;p8':
            p_hdr = create_p([
                {'text': 'Модерация контента дежурным', 'sz': 3000, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=1200, line_spc=110000)
            
            p_body = create_p([
                {'text': 'Все новые заявки перед публикацией в общий доступ поступают дежурному администратору в статус «На модерации». Одобрение в один клик исключает публикацию спама, некорректных фотографий или дубликатов, обеспечивая чистоту базы.', 'sz': 2400, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=125000)
            update_tx_body(sp, [p_hdr, p_body])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide8():
    print("--- Updating Slide 8 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide8.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;99;p9':
            p = create_p([
                {'text': 'Инновация «Профи»: Безопасная передача', 'sz': 3800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;101;p9':
            # Блок 1: Защита от мошенничества и присвоения
            p_hdr = create_p([
                {'text': 'Защита от мошенничества и присвоения', 'sz': 2800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=800, line_spc=110000)
            
            p_body = create_p([
                {'text': 'При создании объявления сервер генерирует уникальный 4-значный проверочный PIN-код. Автор объявления видит этот код у себя и сообщает его владельцу исключительно при очной встрече после проверки примет.', 'sz': 2200, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=120000)
            update_tx_body(sp, [p_hdr, p_body])
            
        elif name == 'Google Shape;100;p9':
            # Блок 2: Двусторонняя верификация без самовозврата
            p_hdr = create_p([
                {'text': 'Двусторонняя верификация без самовозврата', 'sz': 2800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=800, line_spc=110000)
            
            p_body = create_p([
                {'text': 'Получатель вводит код в приложении. Сервер сверяет PIN, переводит вещь в статус «ВОЗВРАЩЕНО» и закрывает сделку. Автор не может закрыть вещь сам себе — подтверждение строго двустороннее.', 'sz': 2200, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=120000)
            update_tx_body(sp, [p_hdr, p_body])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide9():
    print("--- Updating Slide 9 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide9.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;112;p10':
            p = create_p([
                {'text': 'Личный кабинет и мониторинг статусов', 'sz': 3800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;110;p10':
            # 2 блока: статистика и управление своими объявлениями
            p_hdr1 = create_p([
                {'text': 'Прозрачная персональная статистика', 'sz': 2800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=600, line_spc=110000)
            
            p_body1 = create_p([
                {'text': 'Личный кабинет пользователя наглядно показывает счетчики активных вещей («Ищет владельца») и успешно завершенных возвратов («Возвращено»). Доступен быстрый переход ко всем своим объявлениям.', 'sz': 2200, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=1200, line_spc=120000)
            
            p_hdr2 = create_p([
                {'text': 'Управление своими объявлениями', 'sz': 2800, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l', space_aft=600, line_spc=110000)
            
            p_body2 = create_p([
                {'text': 'В карточках собственных вещей автор видит свой секретный PIN-код для передачи. Кнопка ввода кода для автора заблокирована, что гарантирует защиту от фиктивных самовозвратов.', 'sz': 2200, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=120000)
            
            update_tx_body(sp, [p_hdr1, p_body1, p_hdr2, p_body2])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide10():
    print("--- Updating Slide 10 (Chat GIF & Layout) ---")
    rels_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "_rels", "slide10.xml.rels")
    rels_tree = ET.parse(rels_path)
    rels_root = rels_tree.getroot()
    
    # Add relationship for gif_slide10.gif
    has_rel = False
    for rel in rels_root:
        if rel.attrib.get('Target') == '../media/gif_slide10.gif':
            has_rel = True
            break
    if not has_rel:
        new_rel = ET.SubElement(rels_root, '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship', {
            'Id': 'rId6',
            'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
            'Target': '../media/gif_slide10.gif'
        })
        rels_tree.write(rels_path, encoding='utf-8', xml_declaration=True)
        print("Added relationship rId6 -> ../media/gif_slide10.gif")
        
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide10.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    spTree = root.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree')
    
    # Update shapes
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;120;p11':
            # Title
            p = create_p([
                {'text': 'Встроенный чат', 'sz': 4500, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            # Adjust width so it doesn't overlap GIF
            xfrm = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spPr/{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm')
            if xfrm is not None:
                ext = xfrm.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ext')
                if ext is not None:
                    ext.attrib['cx'] = '10200000'
                    
        elif name == 'Google Shape;122;p11':
            # Text description
            p = create_p([
                {'text': 'В карточке каждой вещи доступен встроенный мессенджер. Нашедший и потерявший могут сразу уточнить детали и договориться о месте встречи (например, «Жду у кабинета 12 на перемене») без необходимости передавать личные телефонные номера или искать друг друга в социальных сетях.', 'sz': 2400, 'b': False, 'font': 'Arial', 'color': '1C3354'}
            ], algn='l', line_spc=125000)
            update_tx_body(sp, [p])
            xfrm = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spPr/{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm')
            if xfrm is not None:
                ext = xfrm.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ext')
                if ext is not None:
                    ext.attrib['cx'] = '10200000'
                    ext.attrib['cy'] = '2200000'
                    
    # Adjust diagram position (image23.png)
    for pic in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}pic'):
        blip = pic.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if blip is not None and blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') == 'rId4':
            xfrm = pic.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spPr/{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm')
            if xfrm is not None:
                off = xfrm.find('{http://schemas.openxmlformats.org/drawingml/2006/main}off')
                ext = xfrm.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ext')
                if off is not None and ext is not None:
                    # Place on left below text:
                    off.attrib['x'] = '957150'
                    off.attrib['y'] = '4400000'
                    ext.attrib['cx'] = '10200000'
                    ext.attrib['cy'] = '3888000'
                    print("Adjusted image23.png diagram position on left of Slide 10")
                    
    # Check if GIF pic already exists in spTree
    has_gif_pic = False
    for pic in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}pic'):
        blip = pic.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if blip is not None and blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') == 'rId6':
            has_gif_pic = True
            break
            
    if not has_gif_pic:
        # Create pic XML element identical in structure to other slides
        pic_elem = ET.Element('{http://schemas.openxmlformats.org/presentationml/2006/main}pic')
        
        nvPicPr = ET.SubElement(pic_elem, '{http://schemas.openxmlformats.org/presentationml/2006/main}nvPicPr')
        ET.SubElement(nvPicPr, '{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr', {
            'id': '199', 'name': 'Picture 10', 'descr': 'gif_slide10.gif'
        })
        ET.SubElement(nvPicPr, '{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPicPr', {'preferRelativeResize': '0'})
        ET.SubElement(nvPicPr, '{http://schemas.openxmlformats.org/presentationml/2006/main}nvPr')
        
        blipFill = ET.SubElement(pic_elem, '{http://schemas.openxmlformats.org/presentationml/2006/main}blipFill', {'rotWithShape': '1'})
        blip = ET.SubElement(blipFill, '{http://schemas.openxmlformats.org/drawingml/2006/main}blip', {
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed': 'rId6'
        })
        ET.SubElement(blip, '{http://schemas.openxmlformats.org/drawingml/2006/main}alphaModFix')
        ET.SubElement(blipFill, '{http://schemas.openxmlformats.org/drawingml/2006/main}srcRect')
        ET.SubElement(blipFill, '{http://schemas.openxmlformats.org/drawingml/2006/main}stretch')
        
        spPr = ET.SubElement(pic_elem, '{http://schemas.openxmlformats.org/presentationml/2006/main}spPr')
        xfrm = ET.SubElement(spPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm')
        ET.SubElement(xfrm, '{http://schemas.openxmlformats.org/drawingml/2006/main}off', {
            'x': '11782862', 'y': '114300'
        })
        ET.SubElement(xfrm, '{http://schemas.openxmlformats.org/drawingml/2006/main}ext', {
            'cx': '4526280', 'cy': '10058400'
        })
        
        prstGeom = ET.SubElement(spPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}prstGeom', {'prst': 'rect'})
        ET.SubElement(prstGeom, '{http://schemas.openxmlformats.org/drawingml/2006/main}avLst')
        ET.SubElement(spPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}noFill')
        ln = ET.SubElement(spPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}ln')
        ET.SubElement(ln, '{http://schemas.openxmlformats.org/drawingml/2006/main}noFill')
        
        spTree.append(pic_elem)
        print("Added GIF picture element to Slide 10")
        
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide11():
    print("--- Updating Slide 11 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide11.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is None:
            continue
        name = cNvPr.attrib.get('name', '')
        
        if name == 'Google Shape;142;p12':
            # Block 4 Header
            p = create_p([
                {'text': '100% Отказоустойчивость', 'sz': 3200, 'b': True, 'font': 'Arial', 'color': '000000'}
            ], algn='l')
            update_tx_body(sp, [p])
            
        elif name == 'Google Shape;141;p12':
            # Block 4 Text
            p = create_p([
                {'text': 'Приложение продолжает бесперебойно работать даже при отключении интернета или нестабильном школьном Wi-Fi. Встроенный оффлайн-кэш и снимки данных сохраняют просмотр каталога, поиск и фильтры без белых экранов и вылетов.', 'sz': 2500, 'b': False, 'font': 'Arial', 'color': '000000'}
            ], algn='l', line_spc=125000)
            update_tx_body(sp, [p])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def update_slide12():
    print("--- Updating Slide 12 ---")
    xml_path = os.path.join(UNPACKED_DIR, "ppt", "slides", "slide12.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        cNvPr = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}nvSpPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
        if cNvPr is not None and cNvPr.attrib.get('name') == 'Google Shape;151;p13':
            # Title
            p_title = create_p([
                {'text': 'Итоги: Готовое решение категории «Профи»', 'sz': 3200, 'b': True, 'font': 'Calibri', 'color': '000000'}
            ], algn='l', space_aft=400, line_spc=110000)
            
            # Subtitle
            p_sub = create_p([
                {'text': '100% готовность к промышленному внедрению в центрах «IT-куб» и школах', 'sz': 2200, 'b': True, 'font': 'Calibri', 'color': '1C3354'}
            ], algn='l', space_aft=1200, line_spc=115000)
            
            # Bullet 1
            p_b1 = create_p([
                {'text': '✓ Полное соответствие требованиям: ', 'sz': 2100, 'b': True, 'font': 'Calibri', 'color': '000000'},
                {'text': 'Все критерии базового и профильного уровней Кейса №4 закрыты на 100%.', 'sz': 2100, 'b': False, 'font': 'Calibri', 'color': '333333'}
            ], algn='l', space_aft=600, line_spc=115000)
            
            # Bullet 2
            p_b2 = create_p([
                {'text': '✓ Инновационная безопасность: ', 'sz': 2100, 'b': True, 'font': 'Calibri', 'color': '000000'},
                {'text': 'Механизм Safe Handover по PIN-коду исключает кражу вещей.', 'sz': 2100, 'b': False, 'font': 'Calibri', 'color': '333333'}
            ], algn='l', space_aft=600, line_spc=115000)
            
            # Bullet 3
            p_b3 = create_p([
                {'text': '✓ Высокая инженерная культура: ', 'sz': 2100, 'b': True, 'font': 'Calibri', 'color': '000000'},
                {'text': 'Чистая архитектура, Offline-First, P2P-чат, интеграция с REST API.', 'sz': 2100, 'b': False, 'font': 'Calibri', 'color': '333333'}
            ], algn='l', space_aft=600, line_spc=115000)
            
            # Bullet 4
            p_b4 = create_p([
                {'text': '✓ Продукт готов к релизу: ', 'sz': 2100, 'b': True, 'font': 'Calibri', 'color': '000000'},
                {'text': 'Приложение собрано, протестировано на реальных сценариях и развернуто.', 'sz': 2100, 'b': False, 'font': 'Calibri', 'color': '333333'}
            ], algn='l', line_spc=115000)
            
            update_tx_body(sp, [p_title, p_sub, p_b1, p_b2, p_b3, p_b4])
            
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def main():
    copy_gifs()
    update_slide1()
    update_slide4()
    update_slide5()
    update_slide6()
    update_slide7()
    update_slide8()
    update_slide9()
    update_slide10()
    update_slide11()
    update_slide12()
    print("All slides updated successfully in unpacked_presentation/")

if __name__ == '__main__':
    main()
