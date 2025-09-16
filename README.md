
# Tennis Trainingsplan – Streamlit Viewer

## Dateien
- `app.py` – Die Streamlit-App
- `requirements.txt` – Python-Abhängigkeiten
- **Erwartete CSV**: `/mnt/data/Datum,Tag,Slot,Typ,Spieler.csv` mit den Spalten: `Datum, Tag, Slot, Typ, Spieler`

## Starten (lokal)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Nutzung
- Links in der Sidebar kannst du eine CSV hochladen *oder* die Standarddatei verwenden.
- **Wochenübersicht**: Woche (ISO) auswählen, Zusammenfassung ansehen, CSV exportieren.
- **Spieler-Matches**: Spieler auswählen, Liste & Export.
