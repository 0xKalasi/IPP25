## Implementační dokumentace k 1. úloze do IPP 2024/2025
Jméno a příjmení: Tomáš Bordák\
Login: xborda01

### Hodnotenie
5.5/7
- 60% implementácia (max 6b) 
- docs 

### 1. Implementácia 

V mojej implementácii som použil povolenú knižnicu Lark. LL(1) gramatiku zo zadania, nedefinoval som vlastnú. Podľa Lark dokumentácie, a príkladov v nej, som prepísal spomínanú LL(1) gramatiku aj s definíciami tokenov. 

Lark má hlavnú triedu "Lark", ktorej som predal 3 parametry:
1. definovanú gramatiku
2. začiatočné pravidlo v danej gramatike
3. typ parseru - "lalr"

Následne pomocou inštančnej metódy "parse" na vytvorenej inštancii "parser" sa vytvorí strom z parametru metódy - takto: `` tree = parser.parse( input ) ``, kde "input" je uložený vstup skriptu zo štandardneho vstupu a "tree" je inštanciou triedy Tree. Následne som prechádzal strom v premennej "tree" a analyzoval ho, aby som odhalil možné chyby vo vstupnom kóde.
1. lexikálnú a väčšiu časť syntaktickej analýzy vykonal Lark vďaka definícii gramatiky a tokenov
2. zabezpečil som, ale to už nutným prechodom vygenerovaného stromu, nesprávne použitie kľúčových slov
3. ďalším prechodom stromu som zistil definované triedy, ich metódy a triedu, z ktorej dedia
4. kontrola triedy Main a metody run
5. následne dedenie tried (z tried, z ktorých majú podľa kódu dediť), ošetrenie kruhovej závislosti a pod.
6. sémantická kontrola - posledný prechod stromom (trieda "semanticChecks")
    - kontrola výrazov, 
    - definície premenných,
    - v metode "block" som vyriešil aj kolíziu premenných v bloku s parametrami bloku, aj nedefinované premenné v bloku 

### 2. Rozšírenie
Použil som OOP návrhový vzor "Visitor", vďaka čomu som v rámci Python knižnice Lark mohol definovať akcie, ktoré sa majú vykonať pri prechode kódu pomocou pravidiel v gramatike. Lark obsahuje triedu, ktorá sa volá presne ako návrhový vzor - tiež "Visitor". Niekoľkokrát som si vytvoril novú triedu, ktorá dedí z triedy "Visitor" a upravil metódy, ktoré sú volané pri prechode AST stromom. Tieto metódy majú meno presne ako gramatické pravidlá, tým pádom ako sa prechádza stromom (strom je vytvorený aj s pravidlami), tak sa volali príslušné metódy. Pomocou metódy "visit" sa spustilo prechádzanie daného stromu. Príklad: `` checkKeywords().visit( tree )  ``, "checkKeywords" je mnou definovaná trieda, ktorá dedí z triedy "Visitor" a obsahuje inštančnú metódu "visit". V premmenej "tree" je uložený strom, ktorý je inštanciou triedy "Tree". Tá obsahuje všetky dáta (a metadáta) potrebné pre správne fungovanie triedy "Visitor".

Ďalej som si vytvoril triedu "definedClasses" [viz utils.py], ktorá tiež dedí z triedy "Visitor" a používam ju na:
- definíciu vstavaných tried a ich metód (pri inicializácii inštancie do inštančnej premmenej)
- prvý prechode cez AST, na zistenie v kóde definovaných tried a z akej triedy dedia
    - následne pomocou triednej metódy "inherit" sa vykoná proces dedenia
    - taktiež kontrolujem redefiníciu triedy
    - zaznamenávam si aktuálnu triedu (inštančný atribút) - k nej následne pri prechode cez ďalšie pravidlo systematicky pripájam jej metódy
- vytvoril som inštančnú metódu "checkMain", ktorá pri zavolaní skontroluje definíciu triedy "Main a jej metódy "run" medzi definíciami tried (inštančný atribút "allClasses")
- a ďalej napríklad používam "self" pre odkazovanie na inštanciu

Viem aj o triede "Transformer" z knižnice Lark, ktorá je ale len pre prechod menej efektívna než "Visitor". A to preto, pretože daný strom rekonštruuje pri prechode. Čo sa samozrejme vyplatí, napríklad pri generovaní výstupného XML kódu (zjednodušenie stromu, pre plynulejší prechod a generovanie), ale ku generovaniu som sa bohužial nedostal.

