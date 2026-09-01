rule [
	labelType "term"
	left [
		edge [ source 2 target 6 label "-" ]
		edge [ source 4 target 11 label "-" ]
		edge [ source 8 target 9 label "=" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "O" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 8 label "O" ]
		node [ id 9 label "C" ]
		node [ id 10 label "O" ]
		node [ id 11 label "O" ]
		node [ id 12 label "C" ]
		node [ id 13 label "C" ]
		node [ id 14 label "C" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 12 target 5 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 6 target 7 label "=" ]
		edge [ source 10 target 9 label "=" ]
		edge [ source 11 target 13 label "-" ]
		edge [ source 14 target 2 label "-" ]
	]
	right [
		edge [ source 6 target 8 label "-" ]
		edge [ source 9 target 11 label "-" ]
		edge [ source 8 target 9 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	constrainAdj [
		id 13
		op "="
		count 3
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 12
		op "="
		count 3
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 14
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]