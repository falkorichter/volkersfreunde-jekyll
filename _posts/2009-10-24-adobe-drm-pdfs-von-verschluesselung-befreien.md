---
title: "Adobe DRM – PDFs von Verschlüsselung befreien"
date: 2009-10-24 16:35:38 +0000
permalink: /adobe-drm-pdfs-von-verschluesselung-befreien/
author: "simi"
categories: ["Allgemein"]
tags: []
wp_id: 1079
---
Ein Digital Right Management gibt es mittlerweile nicht nur für Musikdateien sondern auch für digitale Dokumente im pdf-Format. Wie ich erfahren habe, werden solche DRM-geschützten PDFs nicht nur von E-Book-Shops (z.B. Ciando) angeboten, sondern auch von Universitäten (z.B. LMU München) bereit gestellt, um den Studenten auf diese Weise ein “Probelesen” von teuren Büchern zu ermöglichen. Solche PDF-E-Books können dann nicht mehr mit dem PDF Reader, sondern nur noch mit einer speziellen Adobe Software (Adobe Digital Editions, existiert nicht für Linux\!) geöffnet werden. Diese Software sorgt dafür, dass das Buch dann nur ein paar Tage lang betrachtet und auch nicht ausgedruckt werden kann.

<!--more-->

Meine ersten Versuche, diese Sperre (natürlich nur zu Testzwecken) zu umgehen, indem ich einfach diverse (mitunter sehr veraltete) Standalone PDF Reader verwendet habe, schlugen leider fehl. Auch Programme zum Entfernen und Entschlüsseln von PDF Passwörtern (z.B. PDF Password Remover) verweigerten ihren Dienst und meinten nur, sie könnten mit der 128-bit Verschlüsselung nicht umgehen.

Als ich kurz davor war aufzugeben, bin ich auf ein in Python programmiertes Tool namens “Ineptpdf” gestoßen. Wie sich nach langem Hin und Her und einigen Kompilier- und Laufzeitfehlern herausstellte, ist dieses kleine Software-Meisterwerk tatsächlich in der Lage, ein DRM-geschütztes PDF in ein “ganz gewöhnliches” PDF umzuwandeln. Nice\!

Aber um eins klar zu stellen: Das hier soll keine Aufforderung zu illegalen Handluchen sein, es geht hier schließlich nur um den Spaß an der Sache. Aber wie ihr seht, DRM ist – egal ob bei mp3s oder pdfs – sowieso für die Katz. Es wird immer Leute geben, die schlau genug sind, entsprechende Software zu programmieren, um solche “Schutzmechanismen” zu umgehen. 🙂
