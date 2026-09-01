rule [
	labelType "term"
	left [
		edge [ source 16 target 14 label "-" ]
		edge [ source 4 target 9 label "-" ]
	]
	context [
		node [ id 4 label "C" ]
		node [ id 14 label "N" ]
		node [ id 15 label "C" ]
		node [ id 16 label "H" ]
		node [ id 9 label "Br" ]
		node [ id 17 label "H" ]
		edge [ source 14 target 15 label "-" ]
		edge [ source 17 target 14 label "-" ]
	]
	right [
		edge [ source 4 target 14 label "-" ]
		edge [ source 9 target 16 label "-" ]
	]
	constrainAdj [
		id 4
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 15
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 15
		op "="
		count 0
		edgeLabels [ label ":" ]
	]
]