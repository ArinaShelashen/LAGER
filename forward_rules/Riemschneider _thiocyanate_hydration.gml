rule [
	labelType "term"
	left [
		node [ id 4 label "O+" ]
		node [ id 8 label "H" ]
		edge [ source 2 target 3 label "#" ]
		edge [ source 7 target 4 label "-" ]
		edge [ source 4 target 8 label "-" ]
		edge [ source 6 target 4 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
		node [ id 3 label "N" ]
		node [ id 5 label "C" ]
		node [ id 1 label "S" ]
		node [ id 6 label "H" ]
		node [ id 7 label "H" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 1 target 5 label "-" ]
	]
	right [
		node [ id 4 label "O" ]
		node [ id 8 label "H+" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 2 target 4 label "=" ]
		edge [ source 7 target 3 label "-" ]
		edge [ source 6 target 3 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 5
		op "="
		count 0
		nodeLabels [ label "O" label "S" label "N" ]
		edgeLabels [ label "=" ]
	]
]