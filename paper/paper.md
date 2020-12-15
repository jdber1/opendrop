---
title: 'OpenDrop: Open-source software for pendant drop tensiometry & contact angle measurements'
tags:
  - Python
  - pendant drop
  - drop shape analysis
  - tensiometry
  - surface tension
  - interfacial tension
  - contact angle
authors:
  - name: Eugene Huang
    affiliation: 1
  - name: Adam Skoufis
    affiliation: 2
  - name: Terence Denning
    affiliation: 3
  - name: Jianzhong Qi
    orcid: 0000-0001-6501-9050
    affiliation: 3
  - name: Raymond R. Dagastine
    orcid: 0000-0002-2154-4846
    affiliation: 4
  - name: Rico F. Tabor
    orcid: 0000-0003-2926-0095
    affiliation: 2
  - name: Joseph D. Berry
    orcid: 0000-0002-0961-7782
    affiliation: 4
affiliations:
 - name: School of Physics, University of Melbourne, Parkville 3010, Australia
   index: 1
 - name: School of Chemistry, Monash University, Clayton 3800, Australia
   index: 2
 - name: Computing and Information Systems, University of Melbourne, Parkville 3010, Australia
   index: 3
 - name: Department of Chemical Engineering, University of Melbourne, Parkville 3010, Australia
   index: 4
date: 3 February 2020
bibliography: paper.bib
---

# Summary
 Systems where two or more fluids exist in discrete phases
are ubiquitous in nature and in many manufacturing processes. The
common surface (or interface) between two fluids that do not mix
exists in a state of tension, an intrinsic property known as
interfacial tension. The contact angle is another fundamental property of interest when the
interface between two fluids is also in contact with a surface, for
example a water drop resting on a leaf. The contact angle is dependent on the surface energy of the solid and 
describes how liquids spread on a surface – vital information for
dynamic liquid-solid processes such as coating and painting.

Accurate measurements of interfacial tension allow researchers in
industry and academia to make deductions regarding the chemical
composition and crucially, the behavior of the interfaces, enabling
optimal design of devices and processes. In many real formulations or
applied systems, this basic but critical parameter can be quite
challenging to accurately measure. In addition, precise measurements
of the contact angle between a fluid-fluid interface and a solid
surface are critical in order to deduce wetting and spreading
characteristics of liquids on surfaces, and to calculate the surface energy of a solid by measuring the contact angle of a series of liquids on one type of surface. These surface properties are important when considering, to
name two examples, the application of paints to surfaces and
pesticides to plants. It is therefore clear that accurate, rapid and
reproducible measurements of interfacial tension and contact
angle are imperative for effective design, implementation and
optimization of processes involving multiphase systems.

The experimental apparatus required for measurements of interfacial tension and contact angle is conceptually extremely simple, requiring only a needle, a camera, and a light source. The complexity (and associated cost of commercial instruments) comes from the image processing and the complicated numerical algorithm required to calculate these quantities from the acquired experimental image. In 2015, we released OpenDrop, which enables interfacial tension measurements more rapidly, cheaply and accurately than commercial options [@Berry2015]. The only cost to the user is the camera required (approx. $20 - $1K depending upon application), whereas commercial instruments are much more expensive (~$50K). 

Here we present the latest version of OpenDrop. The new version, Barracuda, is able to measure interfacial tension and also contact angle in a variety of configurations with field-leading accuracy and reproducibility. The performance of OpenDrop compared to currently available commercial instrumentation is shown in Figures \autoref{fig:ift} and \autoref{fig:ca}.
The contact angle measurement capability is new for this release, but has been used successfully in previous studies [@Prathapan2017]. OpenDrop has been written in Python because it is open-source, free, runs on multiple operating systems (including Linux, Mac OSX and Windows), and is easily integrable with a large number of mature, 3rd party open source libraries. In particular, OpenDrop utilises the sophisticated image processing capabilities of the OpenCV library in order to extract drop profiles from experimental images for input into the requisite numerical algorithm. Further, the ease of readability and modular nature of Python encourages and supports collaboration, and gives OpenDrop significant pedagogic value. Python can also be easily integrated with other languages, of particular importance to pendant drop tensiometry and contact angle measurements where integration of code needed to control cameras and associated software is a critical requirement. The previous version is in use in many research groups around the world, and is also used in teaching laboratories including Monash University. 

The availability of the software allows the interested user to
effectively implement, explore and further develop the techniques for
both research and teaching at a small fraction of the cost of
commercial options. 

![Comparison of the surface or interfacial tension of different systems calculated with OpenDrop against values reported in the literature.\label{fig:ift}](iftFigure.pdf){ width=20% }

<!-- ![Comparison of the surface or interfacial tension of different systems calculated with OpenDrop against values reported in the literature.\label{fig:ift}](iftFigure.pdf)-->
![Comparison of contact angles calculated from experimental images in the literature against values calculated with commercial instrumentation.The images are taken from [@Nie2017], [@Stacy2009] and [@Brown2016]. \label{fig:ca}](conAnFigure.pdf)


<!-- Consequently, OpenDrop will make significant impact
in both research and education by providing inexpensive access to
high-fidelity information on the stability, function, and behaviour of
interfaces, via a simple and user-friendly interface, with open-source
software that will enable users to implement their own functionality. -->




# Acknowledgements



# References
