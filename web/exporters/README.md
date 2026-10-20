# Exportação sintética de evidências

A partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe web\exporters\export_synthetic.py --release-id synthetic-demo-v2
.\.venv\Scripts\python.exe web\exporters\export_synthetic.py --verify synthetic-demo-v2
```

O ID deve ser novo. A CLI executa testes dos produtores/adaptador, schemas
TypeScript e paridade da grade; só promove JSON completos. Não instala pacotes,
acessa dados externos ou executa avaliação final.

- `web/src/data/releases/<id>/`: agregados e manifesto, candidato pendente.
- `web/reports/export-evidence/<id>/`: auditoria local ignorada pelo Git,
  incluindo representações restritas para conferir hashes. Não publicar.

`--verify` exige o mesmo código/ambiente registrado, recalcula desenvolvimento
sintético em memória e não modifica artefatos existentes.

Consulte [o processo de evidências](../../docs/evidencias-web.md) para indicadores,
denominadores, hipóteses, testes, privacidade, limitações e revisão humana.
