rule [
	labelType "term"
	left [
		edge [ source 12 target 2 label "-" ]
		edge [ source 1 target 13 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "Br" ]
		node [ id 3 label "C" ]
		node [ id 4 label "H" ]
		node [ id 12 label "N" ]
		node [ id 13 label "H" ]
		node [ id 14 label "C" ]
		node [ id 15 label "O" ]
		node [ id 16 label "C" ]
		node [ id 17 label "O" ]
		node [ id 18 label "C" ]
		node [ id 19 label "C" ]
		edge [ source 1 target 3 label "-" ]
		edge [ source 1 target 4 label "-" ]
		edge [ source 12 target 14 label "-" ]
		edge [ source 14 target 15 label "=" ]
		edge [ source 12 target 16 label "-" ]
		edge [ source 16 target 17 label "=" ]
		edge [ source 14 target 18 label "-" ]
		edge [ source 18 target 19 label "-" ]
		edge [ source 19 target 16 label "-" ]
	]
	right [
		edge [ source 1 target 2 label "-" ]
		edge [ source 12 target 13 label "-" ]
	]
	constrainAdj [
		id 3
		op ">="
		count 1
		nodeLabels [ label "C" ]
		edgeLabels [ label ":" label "=" ]
	]
	constrainAdj [
		id 18
		op "="
		count 2
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 19
		op "="
		count 2
		nodeLabels [ label "H" ]
	]
]