rule [
	labelType "term"
	left [
		edge [ source 20 target 24 label "-" ]
		edge [ source 21 target 25 label "-" ]
		edge [ source 12 target 2 label "-" ]
	]
	context [
		node [ id 20 label "S" ]
		node [ id 21 label "S" ]
		node [ id 22 label "C" ]
		node [ id 23 label "C" ]
		node [ id 2 label "Br" ]
		node [ id 12 label "N" ]
		node [ id 14 label "C" ]
		node [ id 15 label "O" ]
		node [ id 16 label "C" ]
		node [ id 17 label "O" ]
		node [ id 18 label "C" ]
		node [ id 19 label "C" ]
		node [ id 24 label "H" ]
		node [ id 25 label "H" ]
		edge [ source 20 target 22 label "-" ]
		edge [ source 21 target 23 label "-" ]
		edge [ source 12 target 14 label "-" ]
		edge [ source 14 target 15 label "=" ]
		edge [ source 12 target 16 label "-" ]
		edge [ source 16 target 17 label "=" ]
		edge [ source 14 target 18 label "-" ]
		edge [ source 18 target 19 label "-" ]
		edge [ source 19 target 16 label "-" ]
	]
	right [
		edge [ source 20 target 21 label "-" ]
		edge [ source 2 target 24 label "-" ]
		edge [ source 12 target 25 label "-" ]
	]
	constrainAdj [
		id 22
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 23
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]