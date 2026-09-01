rule [
	labelType "term"
	left [
		edge [ source 4 target 3 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	context [
		node [ id 1 label "S" ]
		node [ id 2 label "H" ]
		node [ id 3 label "H" ]
		node [ id 4 label "S" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		edge [ source 5 target 1 label "-" ]
		edge [ source 6 target 4 label "-" ]
	]
	right [
		edge [ source 2 target 3 label "-" ]
		edge [ source 1 target 4 label "-" ]
	]
	constrainAdj [
		id 5
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]