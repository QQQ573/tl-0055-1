import requests
import random

brands = ['肯德基', '麦当劳', '华莱士']
complaint_types = ['餐凉', '漏配酱包', '等待过久', '食物变质', '服务态度', '其他']
handlers = ['张三', '李四', '王五', '赵六', '钱七']
compensation_types = ['优惠券', '代金券', '退款', '赠品', '其他']

for i in range(15):
    has_comp = random.choice([True, False])
    amount = random.randint(0, 100) if has_comp else 0
    data = {
        'brand': random.choice(brands),
        'store_code': f'STORE{str(i+1).zfill(3)}',
        'complaint_type': random.choice(complaint_types),
        'handler': random.choice(handlers),
        'has_compensation': has_comp,
        'compensation_type': random.choice(compensation_types) if (has_comp and amount > 0) else None,
        'compensation_amount': amount,
        'is_closed': random.choice([True, False]),
        'closing_remark': '已处理完毕，客户满意' if random.choice([True, False]) else None
    }
    r = requests.post('http://127.0.0.1:8000/tickets', json=data)
    print(f'创建工单 {i+1}: {r.status_code}')

print('\n=== 查询列表（第一页）===')
r = requests.get('http://127.0.0.1:8000/tickets?page=1&page_size=10')
result = r.json()
print(f'总数: {result["total"]}, 本页: {len(result["items"])}')
for item in result['items'][:3]:
    status = '已结案' if item['is_closed'] else '未结案'
    print(f'  [{item["id"]}] {item["brand"]} - {item["complaint_type"]} - {status}')

print('\n=== 筛选品牌=肯德基 ===')
r = requests.get('http://127.0.0.1:8000/tickets?brand=肯德基')
print(f'肯德基工单: {r.json()["total"]} 条')

print('\n=== 筛选未结案 ===')
r = requests.get('http://127.0.0.1:8000/tickets?is_closed=false')
print(f'未结案工单: {r.json()["total"]} 条')
