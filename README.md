# ahha
Albert Heijn Home Assistant integration


Example Card yaml:

```yaml
type: vertical-stack
title: Albert Heijn Uitgaven
cards:
  - type: horizontal-stack
    cards:
      - type: statistic
        entity: sensor.ah_totaal_uitgegeven
        name: Totaal Uitgegeven
        icon: mdi:currency-eur
        stat_type: mean
      - type: statistic
        entity: sensor.ah_totale_korting
        name: Totale Korting
        icon: mdi:percent
  - type: horizontal-stack
    cards:
      - type: statistic
        entity: sensor.ah_aantal_bonnetjes
        name: Aantal Bonnetjes
        icon: mdi:receipt
      - type: statistic
        entity: sensor.ah_gemiddelde_uitgave_per_bonnetje
        name: Gemiddeld per Bonnetje
        icon: mdi:calculator
  - type: entities
    title: Albert Heijn Details
    entities:
      - entity: sensor.ah_laatste_bonnetje
        name: Laatste Bonnetje
        icon: mdi:receipt-text
      - entity: sensor.ah_kortingspercentage
        name: Kortingspercentage
      - entity: sensor.ah_maandelijkse_uitgave
        name: Geschatte Maandelijkse Uitgave
  - type: history-graph
    title: Albert Heijn Uitgaven Trend
    hours_to_show: 168
    refresh_interval: 60
    entities:
      - sensor.ah_totaal_uitgegeven
      - sensor.ah_totale_korting
  - type: markdown
    content: >
      ### 📊 Albert Heijn Statistieken


      **Laatste Update:** {{
      states.sensor.ah_totaal_uitgegeven.last_updated.strftime('%d-%m-%Y %H:%M')
      }}


      **Winkelgegevens laatste bonnetje:**  

      🏪 {{ state_attr('sensor.ah_laatste_bonnetje', 'store_name') }}  

      📍 {{ state_attr('sensor.ah_laatste_bonnetje', 'store_address') }}  

      🧾 Bonnetje #{{ state_attr('sensor.ah_laatste_bonnetje', 'receipt_number')
      }}


      ---


      💡 **Tips:**

      - Gemiddeld bespaar je **{{ states('sensor.ah_kortingspercentage') }}%**
      per aankoop

      - Je koopt gemiddeld **{{ (states('sensor.ah_aantal_bonnetjes') | int /
      4.33) | round(1) }}** keer per maand bij de AH
```
