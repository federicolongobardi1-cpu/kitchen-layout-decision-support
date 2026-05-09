
# Interior Layout Audit MVP - redone

Versione Streamlit rifatta con:
- coffee table rimosso
- piante aggiunte
- divani sistemati e non sovrapposti
- dining set unico invece di tavolo + sedie separate
- frigo aggiunto
- TV unit al posto del vecchio counter nella zona living
- upload spostato nella sidebar per non rompere la schermata iniziale

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Spostamento oggetti

Seleziona un oggetto nel pannello a destra e modifica X/Y con gli slider.
Il layout si aggiorna automaticamente.

## CSV format

```csv
name,type,zone,x,y,w,h
TV Unit,tv,living,40,25,320,38
Sofa 1,sofa,living,55,160,70,175
Dining Set,dining_set,dining,600,145,145,185
```
