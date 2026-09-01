rule [
	labelType "term"
	left [
		edge [ source 1 target 6 label "-" ]
		edge [ source 3 target 5 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "O" ]
		node [ id 4 label "2H" ]
		node [ id 5 label "H" ]
		node [ id 6 label "S" ]
		node [ id 7 label "C" ]
		edge [ source 2 target 1 label "=" ]
		edge [ source 3 target 4 label "-" ]
		edge [ source 7 target 6 label "-" ]
	]
	right [
		edge [ source 1 target 3 label "-" ]
		edge [ source 6 target 5 label "-" ]
	]
	constrainAdj [
		id 7
		op "="
		count 0
		nodeLabels [ label "O" label "C" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 7
		op "<"
		count 3
		nodeLabels [ label "C" ]
	]
]