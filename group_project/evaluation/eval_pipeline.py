"""RAG Evaluation — Accuracy on Golden Set"""
import json, sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.task10_generation import generate_with_citation

dataset = json.load(open('group_project/evaluation/golden_dataset.json', encoding='utf-8'))
results = []
correct = 0

for item in dataset:
    q = item['question']
    expected = item['answer'].lower()
    gen = generate_with_citation(q, top_k=5)
    answer = gen['answer'].lower()
    keywords = [w for w in expected.split() if len(w) > 2]
    passed = sum(1 for kw in keywords if kw in answer) >= max(1, len(keywords) // 3)
    if passed: correct += 1
    results.append({'q': q[:50], 'exp': expected[:50], 'pass': passed})

accuracy = correct / len(dataset) * 100

with open('group_project/evaluation/results.md', 'w', encoding='utf-8') as f:
    f.write(f'# CP3 — Ket qua danh gia RAG\n\nGolden set: {len(dataset)} | Passed: {correct}/{len(dataset)} ({accuracy:.0f}%)\n\n')
    f.write('| # | Question | Expected | Pass |\n|---|----------|----------|------|\n')
    for i, r in enumerate(results):
        f.write(f'| {i+1} | {r["q"]} | {r["exp"]} | {"PASS" if r["pass"] else "FAIL"} |\n')

print(f'Golden set: {len(dataset)} | Passed: {correct}/{len(dataset)} ({accuracy:.0f}%)')
