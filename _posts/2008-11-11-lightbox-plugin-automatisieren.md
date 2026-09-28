---
title: "Lightbox plugin automatisieren"
date: 2008-11-11 01:26:02 +0000
permalink: /lightbox-plugin-automatisieren/
author: "andy"
categories: ["Allgemein", "Technik/Software"]
tags: ["lightbox", "plugin", "wordpress"]
wp_id: 810
---
Ich habe mich in letzter Zeit schon öfter gefragt, warum man bei einzelnen Bildern das rel-Tag für lightbox manuell hinzufügen muss, während es bei Galerien z.B. automatisch funktioniert. Nun hab ich die Lösung. Wenn man sich die Readme.txt zum jeweiligen lightbox-plugin ansieht, steht dort auch schon die Lösung: in der entsprechenden lightbox.php bzw. lightbox2.php Plugin-Datei in den nötigen Zeilen einfach den Kommentar entfernen (bei mir Zeile 21-24 und schon läufts.

Dies ist aber anscheinend nicht bei allen lightbox-plugins erforderlich, denn bei einigen ist das standardmäßig schon drin… Naja, nützlich ist es allemal\!
