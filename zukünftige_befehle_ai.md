Ich denke du hast den Einrasten-Button nicht ganz richtig implementiert. Ich kann objekte nur verschieben wenn der Einrasten button deaktiviert ist, aber das EInrasten soll eigentlich die funktion haben dass objekte automatisch an ihre richtige position snappen (wand an andere wandkanten oben unten links und rechts, bzw wenn eine wand gedreht ist soll die pivotecke sich immer an existierenden wänden entlangschieben. fenster und türen sollen dann nur in wänden platzierbar sein, dächer auf wänden und böden an wänden auf y=0)

bauteile werden derzeit an der hinteren linken ecke auf 0 0 0 gesetzt, es soll aber an der vorderen linken ecke auf 0 0 0 sein

mache die kamerasteuerung etwas weniger sensibel. möglichst auf standardeinstellungen falls die anders sind als jetzt gerade.

Das Dach soll auch dreidimensional entlang der Kante geschoben werden. 

Das Dach soll auch schräg entlang von Wänden geschoben werden.

Bei der ersten eingabe der Position wird diese noch nicht verändert, erst bei der zweiten eingabe. versuche eine ressourcen
Das Import und Export Emoji geht nicht mehr, das davor war super und ging. Mache die Seitenleiste etwas kompakter. vorallem leeren Abstände nehmen etwas Platz weg. Du kannst auch alle Abschnitte immer ganz leicht hellgrau hinterlegen, damit man sieht dass es zusammengehört (also zB Gebäude, Neues Bauteil, Bauteil-Übersicht).

Statt Eigenschaften soll beim Ghost und beim normalen Eigenschaftsfenster jetzt der Typ auf deutsch stehen. Dann kann die alte Typ-Box weg.

Mach die Kameraführung sanfter, am besten auf Standardeinstellungen falls es das gibt.

Ich will den Werkstoff von einem Bauteil auswählen können. Dabei greife ich auf die Werkstoffdatenbank zu.

Ich will die größe des "verschieben" buttons verändern und rechts daneben einen zweiten button einfügen. Dieser soll die "Einrasten"-Funktion ermöglichen und standardmäßig an sein. Wenn ich ein Fenster oder eine Tür bewege, sollen diese automatisch automatisch nur in wänden platziert werden können. Wenn ich eine Wand bewege, soll diese automatische an die nächste wand nahtlos "andocken" / bzw. einrasten.

Es soll einen neuen Button "Neues Gebäude" direkt über dem Import-Button geben. Hier soll es die Möglichkeit geben, eine Länge, Breite, Geschosshöhe und Geschosszahl einzugeben, und bei 

Der Löschen Button im Eigenschaften-Panel funktioniert noch nicht.


------------------------------------------------------------------------------------

Schaue dir nochmal die standards.py-Datei an. Mache eine Eingabe der für die Norm wichtigen Parameter. Eventuell werden diese auch schon in der simulation angegeben Möglichkeit 

pkill -f "python.*run.py" 
integrieren

kann der building_editor nicht gelöscht werden? Räume das ui verzeichnis auf. Es soll nichts mehr advanced oder enhanced heißen. Alles sollen nur prägnante, kurze Namen sein.

lies dir zuerst die gesamte ui-struktur und den gesamten code durch, um dann individuell basierend auf diesem code verbesserungen in diesem chatfenster erstellen zu können. zeige mir nicht was du machst. nur am ende eine sehr kurze, prägnante beschreibung dessen was du erreicht/nicht erreicht hast.

Das debug-log muss auch wieder rein. außerdem will ich auf der linken seite ein ausfaltbares menü für PV-Anlage, Wärmepumpe, Simulation,  
