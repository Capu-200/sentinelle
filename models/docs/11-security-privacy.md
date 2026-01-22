# 11 — Sécurité & confidentialité (baseline)

## Principe

Le moteur se limite à des signaux transactionnels et comportementaux.

- pas de données personnelles directes
- minimisation : ne collecter / stocker / logger que le nécessaire

## Données interdites (à compléter)

À compléter avec la liste exacte (cf. `docs/09-open-questions.md`).

Exemples typiques (souvent interdits ou à anonymiser fortement) :

- IP brute (préférer un hash/prefix ou une géoloc “coarse”)
- GPS précis (préférer pays/ville)
- device fingerprint complet (préférer un identifiant pseudonymisé)
- noms, emails, numéros de téléphone, adresses

## Logging

- logs structurés
- redaction obligatoire si un champ peut contenir des PII (ex: payload brut fournisseur)

