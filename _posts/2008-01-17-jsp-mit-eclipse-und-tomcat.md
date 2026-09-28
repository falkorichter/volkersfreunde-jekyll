---
title: "JSP mit Eclipse und Tomcat"
date: 2008-01-17 13:29:35 +0000
permalink: /jsp-mit-eclipse-und-tomcat/
author: "simi"
categories: ["Technik/Software"]
tags: ["tutorial"]
wp_id: 410
---
Bei der Programmierung der abschließenden Belegarbeit4 unserer DB-Vorlesung empfiehlt es sich, die JSP-Anwendung mit Eclipse zu entwerfen, so dass man auch auf den gewohnten “Eclipse-Komfort” nicht verzichten muss.  
Damit das alles funktioniert, ist es sinnvoll, den Tomcat-Server in Eclipse zu integrieren. Die folgenden Schritte sollen kurz darstellen, wie ich bei der Einrichtung vorgegangen bin, so dass die von Herrn Langbein zur Verfügung gestellten Scripte lauffähig sind:

<!--more-->

**1. MySQL-Datenbank vorbereiten**  
Damit die Beispiel-Dateien funktionieren, sollte man natürlich die SQL-Tabellen, auf welchen die Beispiele basieren, auch in der eigenen Datenbank anlegen. Die nötige sql-Datei ist im war-Archiv bei jedem Beispiel integriert.

**2. Tomcat installieren**  
Eine Windows-Installationsdatei für den aktuellen Apache Tomcat gibt es z.B. [hier](http://apache.autinity.de/tomcat/tomcat-6/v6.0.14/bin/apache-tomcat-6.0.14.exe).

**3. Eclipse Plugin installieren**  
Das Plugin, welches ich verwendete, heißt “[Sysdeo/SQLI Eclipse Tomcat Launcher plugin](http://www.eclipsetotale.com/tomcatPlugin/tomcatPluginV321.zip)“. Die zip-Datei einfach in das plugin-Verzeichnis von Eclipse entpacken.

**4. Tomcat-Plugin einrichten**  
Nachdem man Eclipse nun gestartet hat, muss man das Tomcat-Plugin einrichten, d.h. dem Puglin mitteilen, wo das Installationsverzeichnis von Tomcat liegt: In Eclipse unter “Preferences”-\>”Tomcat” bei “Tomcat Home” das entspr. Verzeichnis wählen.

**5. Tomcat-Projekt erstellen**  
Nun kann man ein neues Projekt starten. Als Projekttyp einfach unter “Java” den Punkt “Tomcat Projekt” wählen. In das neue Projektverzeichnis könnt ihr die Dateien aus einem von Herrn Langbein bereitgestellten war-Archiven kopieren und diese dann in Eclipse bearbeiten (achtet auf die von Herrn Langbein vorgegebenen package-Namen).  
Damit die Beispiele eine Verbindung zur Datenbank herstellen können, braucht Eclipse die nötigen jdbc-Treiber. Dazu müsst ihr die “mysql-connector….”.jar-Datei, welche im lib-Ordner des war-Archivs liegt, zum Java Build Path hinzufügen, beispielsweise durch Rechtsklick auf die Datei im Package Exlorer und durch Wählen von “Build Path”-\>”Add to Build Path”. Wenn ihr nun noch die DB-Verbindung im Konstruktor der DBZugriff.java mit euren eigenen Mysql-Zugangsdaten ersetzt und im Eclipse-Menü “Tomcat” den Tomcat-Server startet, müsste alles klappen.  
Sobald ihr die java-Datei speichert, wird automatisch im WEB-INF-Verzeichnis “classes” die entspr. class-Datei kompiliert (so wars zumindest bei mir).

**6. jsp-Dateien im Browser anzeigen**  
Wenn eurer Tomcat-Server korrekt läuft, müsstet ihr über / die Startseite des Tomcat-Servers erreichen. Eclipse ändert die Tomcat-Konfiguration so ab, dass er automatisch das Tomcat-Webapps-Verzeichnis auf euren Eclipse-Workspace legt. So könnt ihr eure jsp-Datei ganz einfach erreichen über:  
/*Projektname*/*dateiname.jsp*

Evtl. auftretende Fehlermeldungen beim Ausführen der jsp-Datei werden in ausführlicher Form in der Konsole von Eclipse wiedergegeben.

Na denn, Viel Erfolg\!

Bei Problemen hilft euch evtl. [diese Anleitung](http://plato.acadiau.ca/courses/comp/dsilver/2513/EclipseAndTomcatTutorial/) weiter.
