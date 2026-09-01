rule [
	labelType "term"
	left [
		edge [ source 6 target 2 label "-" ]
		edge [ source 6 target 8 label "-" ]
		edge [ source 9 target 10 label "-" ]
		edge [ source 11 target 9 label "-" ]
	]
	context [
		node [ id 2 label "Cl" ]
		node [ id 6 label "S" ]
		node [ id 7 label "O" ]
		node [ id 8 label "Cl" ]
		node [ id 9 label "N" ]
		node [ id 10 label "H" ]
		node [ id 11 label "H" ]
		node [ id 12 label "C" ]
		edge [ source 6 target 7 label "=" ]
		edge [ source 9 target 12 label "-" ]
	]
	right [
		edge [ source 9 target 6 label "=" ]
		edge [ source 10 target 8 label "-" ]
		edge [ source 11 target 2 label "-" ]
	]
	constrainAdj [
		id 12
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]