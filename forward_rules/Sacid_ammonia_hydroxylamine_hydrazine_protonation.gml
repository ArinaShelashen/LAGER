rule [
	left [
		node [ id 1 label "N" ]
		node [ id 3 label "O" ]
		edge [ source 2 target 3 label "-" ]
	]
	context [
		node [ id 2 label "H" ]
		node [ id 4 label "S" ]
		edge [ source 3 target 4 label "-" ]
	]
	right [
		node [ id 1 label "N+" ]
		node [ id 3 label "O-" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 4
		op ">="
		count 2
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 1
		op "="
		count 3
		nodeLabels [ label "N" label "O" label "H" ]
		edgeLabels [ label "-" ]
	]
]