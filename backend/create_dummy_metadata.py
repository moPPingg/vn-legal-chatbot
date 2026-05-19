import json
import os
from datetime import datetime

metadata = [
    {'so_hieu': '168/2024/NĐ-CP', 'slug': '168-2024-ND-CP', 'ten_van_ban': 'Nghị định 168/2024/NĐ-CP Quy định chi tiết một số điều của Luật Trật tự, an toàn giao thông đường bộ', 'tinh_trang': 'Còn hiệu lực', 'ngay_ban_hanh': '31/12/2024'},
    {'so_hieu': '100/2019/NĐ-CP', 'slug': '100-2019-ND-CP', 'ten_van_ban': 'Nghị định 100/2019/NĐ-CP Quy định xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ và đường sắt', 'tinh_trang': 'Còn hiệu lực', 'ngay_ban_hanh': '30/12/2019'},
    {'so_hieu': '123/2021/NĐ-CP', 'slug': '123-2021-ND-CP', 'ten_van_ban': 'Nghị định 123/2021/NĐ-CP sửa đổi các Nghị định quy định xử phạt vi phạm hành chính trong lĩnh vực hàng hải, giao thông đường bộ', 'tinh_trang': 'Còn hiệu lực', 'ngay_ban_hanh': '28/12/2021'},
    {'so_hieu': '46/2016/NĐ-CP', 'slug': '46-2016-ND-CP', 'ten_van_ban': 'Nghị định 46/2016/NĐ-CP quy định xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ', 'tinh_trang': 'Hết hiệu lực', 'ngay_ban_hanh': '26/05/2016'},
    {'so_hieu': '15/2003/NĐ-CP', 'slug': '15-2003-ND-CP', 'ten_van_ban': 'Nghị định 15/2003/NĐ-CP quy định xử phạt vi phạm hành chính về giao thông đường bộ', 'tinh_trang': 'Hết hiệu lực', 'ngay_ban_hanh': '19/02/2003'}
]

for item in metadata:
    item['domain'] = 'giao_thong'
    item['pdf_api_url'] = f'/api/document/giao_thong/{item["slug"]}.pdf'
    item['pdf_local_path'] = f'storage/pdfs/giao_thong/{item["slug"]}.pdf'
    
    with open(f'storage/raw/giao_thong/{item["slug"]}.json', 'w', encoding='utf-8') as f:
        json.dump(item, f, ensure_ascii=False, indent=2)
