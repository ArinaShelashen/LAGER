rule [
	labelType "term"
	left [
		edge [ source 3 target 4 label "=" ]
		edge [ source 6 target 7 label "-" ]
		edge [ source 8 target 2 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 5 label "O" ]
		node [ id 6 label "N" ]
		node [ id 7 label "H" ]
		node [ id 8 label "H" ]
		node [ id 10 label "C" ]
		node [ id 9 label "C" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 4 target 5 label "=" ]
		edge [ source 10 target 6 label "-" ]
		edge [ source 9 target 6 label "-" ]
	]
	right [
		edge [ source 3 target 4 label "-" ]
		edge [ source 7 target 8 label "-" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 2 target 3 label "-" ]
	]
	constrainAdj [
		id 1
		op ">="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainAdj [
		id 2
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 10
		op "="
		count 0
		nodeLabels [ label "O" label "S" label "P" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 9
		op "="
		count 0
		nodeLabels [ label "O" label "S" label "P" ]
		edgeLabels [ label "=" ]
	]
]