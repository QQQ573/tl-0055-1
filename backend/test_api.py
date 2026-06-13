import requests
import json

print('=== 测试新 API ===')
print()

print('1. 版本检查:')
r = requests.get('http://127.0.0.1:8000/')
print(f'  {r.json()}')
print()

print('2. SLA 配置:')
r = requests.get('http://127.0.0.1:8000/sla-config')
print(f'  {json.dumps(r.json(), indent=2, ensure_ascii=False)}')
print()

print('3. 状态配置:')
r = requests.get('http://127.0.0.1:8000/statuses')
print(f'  {json.dumps(r.json(), indent=2, ensure_ascii=False)}')
print()

print('4. 动作类型:')
r = requests.get('http://127.0.0.1:8000/actions')
print(f'  {json.dumps(r.json(), indent=2, ensure_ascii=False)}')
print()

print('5. 创建测试工单:')
data = {
    'brand': '肯德基',
    'store_code': 'TEST001',
    'complaint_type': '等待过久',
    'handler': '测试员',
    'has_compensation': False,
    'compensation_amount': 0,
    'is_closed': False
}
r = requests.post('http://127.0.0.1:8000/tickets', json=data)
print(f'  Status: {r.status_code}')
ticket = r.json()
print(f'  ID: {ticket["id"]}')
print(f'  Status: {ticket["status"]}')
ticket_id = ticket['id']
print()

print('6. 状态流转测试:')
print('  6.1 受理工单:')
r = requests.post(f'http://127.0.0.1:8000/tickets/{ticket_id}/transition', json={'action': 'accept'})
print(f'    Status: {r.status_code}, Message: {r.json()}')

r = requests.get(f'http://127.0.0.1:8000/tickets/{ticket_id}')
print(f'    新状态: {r.json()["status"]}')
print()

print('  6.2 提交复核:')
r = requests.post(f'http://127.0.0.1:8000/tickets/{ticket_id}/transition', json={'action': 'review'})
print(f'    Status: {r.status_code}, Message: {r.json()}')

r = requests.get(f'http://127.0.0.1:8000/tickets/{ticket_id}')
print(f'    新状态: {r.json()["status"]}')
print()

print('7. 查看操作日志:')
r = requests.get(f'http://127.0.0.1:8000/tickets/{ticket_id}/logs')
logs = r.json()
print(f'  总共 {len(logs)} 条日志:')
for log in logs:
    print(f'    - {log["action"]}: {log["operator"]} @ {log["created_at"]}')
    if log['remark']:
        print(f'      备注: {log["remark"]}')
print()

print('8. 测试驳回（应该失败）:')
r = requests.post(f'http://127.0.0.1:8000/tickets/{ticket_id}/transition', json={'action': 'reject'})
print(f'  Status: {r.status_code}')
if r.status_code == 400:
    print(f'  错误信息: {r.json()["detail"]}')
print()

print('9. 正确驳回:')
r = requests.post(f'http://127.0.0.1:8000/tickets/{ticket_id}/transition', json={'action': 'reject', 'rejected_reason': '需要补充证据'})
print(f'  Status: {r.status_code}, Message: {r.json()}')

r = requests.get(f'http://127.0.0.1:8000/tickets/{ticket_id}')
ticket = r.json()
print(f'  新状态: {ticket["status"]}')
print(f'  驳回原因: {ticket["rejected_reason"]}')
print()

print('10. 查看最新的操作日志:')
r = requests.get(f'http://127.0.0.1:8000/tickets/{ticket_id}/logs')
logs = r.json()
print(f'  总共 {len(logs)} 条日志:')
for log in logs[:3]:
    print(f'    - {log["action"]}: {log["operator"]}')
    print(f'      备注: {log["remark"]}')
print()

print('=== 测试完成 ===')
