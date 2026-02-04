#!/bin/bash

# 清理测试知识库数据

BASE_URL="http://127.0.0.1:8000/api"

echo "获取所有知识库..."
kbs=$(curl -s "${BASE_URL}/knowledge-bases/")

# 提取所有 ID
ids=$(echo "$kbs" | python3 -c "import sys, json; data = json.load(sys.stdin); print(' '.join([kb['id'] for kb in data]))")

echo "找到 $(echo $ids | wc -w) 个知识库"
echo ""

for id in $ids; do
    # 获取知识库名称
    name=$(echo "$kbs" | python3 -c "import sys, json; data = json.load(sys.stdin); kb = next((k for k in data if k['id'] == '$id'), None); print(kb['name'] if kb else '')")
    
    echo "删除: $name (ID: $id)"
    curl -s -X DELETE "${BASE_URL}/knowledge-bases/${id}"
    echo " ✓"
done

echo ""
echo "清理完成！"
