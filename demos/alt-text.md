# Output Formats and Alt Text

*2026-02-14T16:42:03Z*

This demo shows chartroom's output format options (`-f` / `--output-format`) and smart auto-generated alt text. Each chart is generated with `-f alt` to show the alt text that would be embedded in markdown, HTML, or JSON output.

## Bar Chart — Small Dataset

With a small dataset, the alt text lists every value:

```bash {image}
echo "name,value
alice,10
bob,20
charlie,15" > /tmp/small.csv && uv run chartroom bar --csv /tmp/small.csv -o demos/bar-small.png --title "Team Scores"
```

![14184d5c-2026-02-14](14184d5c-2026-02-14.png)

```bash
echo "name,value
alice,10
bob,20
charlie,15" > /tmp/small.csv && uv run chartroom bar --csv /tmp/small.csv -o /tmp/bar-small.png -f alt
```

```output
Bar chart of value by name — alice: 10, bob: 20, charlie: 15
```

## Bar Chart — Large Dataset

With more data points, the alt text summarizes instead of listing everything:

```bash {image}
python3 -c "
import csv, sys
w = csv.writer(sys.stdout)
w.writerow([\"city\",\"population\"])
cities = [(\"Tokyo\",37400),(\"Delhi\",30290),(\"Shanghai\",27058),(\"São Paulo\",22043),(\"Mexico City\",21782),(\"Cairo\",20901),(\"Mumbai\",20411),(\"Beijing\",20384),(\"Dhaka\",17118),(\"Osaka\",19165)]
for c,p in cities:
    w.writerow([c,p])
" > /tmp/cities.csv && uv run chartroom bar --csv /tmp/cities.csv -o demos/bar-large.png -x city -y population
```

![2522e535-2026-02-14](2522e535-2026-02-14.png)

```bash
uv run chartroom bar --csv /tmp/cities.csv -o /tmp/bar-large.png -x city -y population -f alt
```

```output
Bar chart of population by city. 10 points, ranging from 17118 (Dhaka) to 37400 (Tokyo)
```

## Pie Chart
