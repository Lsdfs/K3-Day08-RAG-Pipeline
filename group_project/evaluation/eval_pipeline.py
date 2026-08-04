"""RAG Evaluation Pipeline — CP3 Results"""
import json, sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import generate_with_citation

dataset = json.load(open('group_project/evaluation/golden_dataset.json', encoding='utf-8'))
results = []
correct = 0

for item in dataset:
    q = item['question']
    expected = item['expected_answer'].lower()
    gen = generate_with_citation(q, top_k=3)
    answer = gen['answer'].lower()
    keywords = [w for w in expected.split() if len(w) > 2]
    passed = sum(1 for kw in keywords if kw in answer) >= len(keywords) // 3
    if passed: correct += 1
    results.append({'q': q[:60], 'exp': expected[:60], 'pass': passed, 'src': gen.get('retrieval_source','-')})

accuracy = correct / len(dataset) * 100

with open('group_project/evaluation/results.md', 'w', encoding='utf-8') as f:
    f.write(f'# CP3 - Ket qua luot 1\n\n')
    f.write(f'Golden set: {len(dataset)} cases | Passed: {correct}/{len(dataset)} ({accuracy:.1f}%)\n\n')
    f.write('| # | Question | Expected | Pass | Source |\n')
    f.write('|---|----------|----------|------|--------|\n')
    for i, r in enumerate(results):
        f.write(f'| {i+1} | {r["q"]} | {r["exp"]} | {"PASS" if r["pass"] else "FAIL"} | {r["src"]} |\n')

print(f'Golden set: {len(dataset)} | Passed: {correct}/{len(dataset)} ({accuracy:.1f}%)')
print('Done.')
