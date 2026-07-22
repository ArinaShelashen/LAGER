rule [
	left [
		edge [ source 3 target 4 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "O" ]
		node [ id 6 label "2H" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 5 target 1 label "=" ]
	]
	right [
		edge [ source 3 target 1 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 2
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 3
		op ">="
		count 1
		edgeLabels [ label ":" ]
	]
]