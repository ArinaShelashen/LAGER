rule [
	labelType "term"
	left [
		edge [ source 0 target 1 label "-" ]
		edge [ source 7 target 5 label "-" ]
	]
	context [
		node [ id 0 label "S" ]
		node [ id 1 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 5 label "N" ]
		node [ id 6 label "C" ]
		node [ id 7 label "H" ]
		node [ id 8 label "H" ]
		edge [ source 0 target 4 label "-" ]
		edge [ source 1 target 3 label "=" ]
		edge [ source 6 target 5 label "-" ]
		edge [ source 8 target 5 label "-" ]
	]
	right [
		edge [ source 7 target 0 label "-" ]
		edge [ source 5 target 1 label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
	constrainAdj [
		id 1
		op "="
		count 1
		nodeLabels [ label "C" label "H" ]
	]
]