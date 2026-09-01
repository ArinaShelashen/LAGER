rule [
	labelType "term"
	left [
		edge [ source 6 target 2 label "-" ]
		edge [ source 11 target 9 label "-" ]
		edge [ source 14 target 13 label "-" ]
		edge [ source 6 target 8 label "-" ]
	]
	context [
		node [ id 2 label "Cl" ]
		node [ id 6 label "S" ]
		node [ id 7 label "O" ]
		node [ id 8 label "Cl" ]
		node [ id 9 label "N" ]
		node [ id 10 label "C" ]
		node [ id 11 label "H" ]
		node [ id 12 label "C" ]
		node [ id 13 label "N" ]
		node [ id 14 label "H" ]
		node [ id 15 label "C" ]
		node [ id 16 label "C" ]
		edge [ source 6 target 7 label "=" ]
		edge [ source 9 target 12 label "-" ]
		edge [ source 9 target 10 label "-" ]
		edge [ source 15 target 13 label "-" ]
		edge [ source 16 target 13 label "-" ]
	]
	right [
		edge [ source 9 target 6 label "-" ]
		edge [ source 11 target 2 label "-" ]
		edge [ source 6 target 13 label "-" ]
		edge [ source 8 target 14 label "-" ]
	]
	constrainAdj [
		id 10
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 12
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
		constrainAdj [
		id 15
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 16
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]