rule [
	labelType "term"
	left [
		edge [ source 6 target 9 label "-" ]
		edge [ source 9 target 7 label "-" ]
		edge [ source 7 target 6 label "-" ]
	]
	context [
		node [ id 1 label "P" ]
		node [ id 2 label "C" ]
		node [ id 3 label "C" ]
		node [ id 4 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "C" ]
		node [ id 9 label "O" ]
		edge [ source 2 target 1 label "-" ]
		edge [ source 1 target 3 label "-" ]
		edge [ source 4 target 1 label "-" ]
	]
	right [
		edge [ source 9 target 1 label "=" ]
		edge [ source 7 target 6 label "=" ]
	]
	constrainAdj [
		id 2
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainAdj [
		id 3
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainAdj [
		id 4
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
]