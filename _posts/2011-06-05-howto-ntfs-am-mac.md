---
title: "HowTo: NTFS am Mac"
date: 2011-06-05 12:48:51 +0000
permalink: /howto-ntfs-am-mac/
author: "andy"
categories: ["Aus dem Netz gefischt", "Buzz der Woche", "Technik/Software"]
tags: ["mac", "ntfs"]
wp_id: 1332
---
Jaja, das leidige Thema Kompatibilität der Dateisysteme und Austausch unter den verschiedenen Betriebssystemen. Mittlerweile möchte man meinen, dass alles schon out-of-the-box funktionieren sollte, aber weit gefehlt. Wer am Mac eine NTFS-Partition, z.B. auf einer externen Festplatte, beschreiben will, braucht zwingend einen passenden Treiber, ansonsten bleibt man beschränkt auf den lesenden Zugriff.

<!--more-->

Um den Zugriff zu realisieren, gibt es verschiedene Treiber, entweder open source oder doch für ein paar Euros zu erwerben. Ich habe mich für die kostenlose Variante entschieden und mit Hilfe [dieser Anleitung](http://board.gulli.com/thread/934413-plugampplay-write-ntfs-with-leopard-mac/) endlich den Zugriff erfolgreich hinbekommen.

Kurz zusammengefasst: MacFuse installieren, Neustarten, NTFS-3G installieren, Neustarten, Fertig. Die auf der Seite verlinkten Versionen funktionieren auf einem aktuellen Leo aber nicht mehr, deshalb unbedingt gleich die aktuellen Treiberversionen aus dem Netz ziehen:

– MacFuse: [http://code.google.com/p/macfuse/](http://code.google.com/p/macfuse/)

– NTFS-3G: h[ttp://sourceforge.net/projects/catacombae/files/NTFS-3G%20for%20Mac%20OS%20X/2010.10.2/ntfs-3g-2010.10.2-macosx.dmg/download](http://sourceforge.net/projects/catacombae/files/NTFS-3G%20for%20Mac%20OS%20X/2010.10.2/ntfs-3g-2010.10.2-macosx.dmg/download)

Nach einem Neustart (ja man glaubt es kaum, aber es ist wahr\!) findet sich dann unter “Informationen” zur entsprechender Festplatte als Format “NTFS-3g (MacFUSE)”.

Damit steht dem Lese- und Schreibvorgängen nun nichts mehr im Wege.
