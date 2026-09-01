rule [
	labelType "term"
	left [
		edge [ source 6 target 2 label "-" ]
		edge [ source 11 target 9 label "-" ]
		edge [ source 9 target 10 label "-" ]
		edge [ source 12 target 10 label "=" ]
		edge [ source 13 target 9 label "-" ]
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
		node [ id 12 label "O" ]
		node [ id 13 label "H" ]
		edge [ source 6 target 7 label "=" ]
	]
	right [
		edge [ source 11 target 2 label "-" ]
		edge [ source 9 target 10 label "#" ]
		edge [ source 13 target 8 label "-" ]
		edge [ source 12 target 6 label "=" ]
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
]