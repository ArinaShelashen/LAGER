rule [
	labelType "term"
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 6 target 7 label "-" ]
		edge [ source 7 target 9 label "-" ]
	]
	context [
		node [ id 1 label "N" ]
		node [ id 2 label "H" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 5 label "O" ]
		node [ id 6 label "O" ]
		node [ id 7 label "C" ]
		node [ id 8 label "O" ]
		node [ id 9 label "O" ]
		node [ id 10 label "C" ]
		node [ id 11 label "C" ]
		edge [ source 3 target 4 label "-" ]
		edge [ source 3 target 10 label "-" ]
		edge [ source 4 target 5 label "=" ]
		edge [ source 7 target 8 label "=" ]
		edge [ source 9 target 11 label "-" ]
	]
	right [
		edge [ source 1 target 4 label "-" ]
		edge [ source 2 target 9 label "-" ]
		edge [ source 6 target 7 label "=" ]
	]
	constrainAdj [
		id 1
		op "="
		count 2
		nodeLabels [ label "N" label "C" ]
		edgeLabels [ label ":" ]
	]
]