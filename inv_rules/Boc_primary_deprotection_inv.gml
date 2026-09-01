rule [
	labelType "term"
	left [

		edge [ source 5 target 6 label "=" ]
		edge [ source 13 target 16 label "=" ]
		edge [ source 18 target 2 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 5 label "O" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 13 label "C" ]
		node [ id 2 label "N" ]
		node [ id 15 label "C" ]
		node [ id 16 label "C" ]
		node [ id 17 label "C" ]
		node [ id 18 label "H" ]
		node [ id 20 label "H" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 6 target 7 label "=" ]
		edge [ source 15 target 13 label "-" ]
		edge [ source 17 target 13 label "-" ]
		edge [ source 20 target 2 label "-" ]
	]
	right [
		edge [ source 2 target 6 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 13 target 16 label "-" ]
		edge [ source 13 target 5 label "-" ]
		edge [ source 16 target 18 label "-" ]
	]
	constrainAdj [
		id 17
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 15
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 16
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]