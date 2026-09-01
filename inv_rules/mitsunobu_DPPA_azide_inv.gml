rule [
	labelType "term"
	left [
		edge [ source 1 target 4 label "-" ]
		edge [ source 6 target 2 label "=" ]
		edge [ source 7 target 8 label "-" ]
		edge [ source 7 target 3 label "-" ]
		edge [ source 8 target 20 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "H" ]
		node [ id 4 label "N" ]
		node [ id 6 label "P" ]
		node [ id 10 label "C" ]
		node [ id 11 label "C" ]
		node [ id 12 label "C" ]
		node [ id 7 label "N" ]
		node [ id 8 label "N" ]
		node [ id 13 label "C" ]
		node [ id 14 label "O" ]
		node [ id 15 label "C" ]
		node [ id 16 label "O" ]
		node [ id 20 label "P" ]
		node [ id 21 label "O" ]
		node [ id 22 label "O" ]
		node [ id 23 label "O" ]
		edge [ source 6 target 10 label "-" ]
		edge [ source 6 target 11 label "-" ]
		edge [ source 6 target 12 label "-" ]
		edge [ source 7 target 13 label "-" ]
		edge [ source 13 target 14 label "=" ]
		edge [ source 8 target 15 label "-" ]
		edge [ source 15 target 16 label "=" ]
		edge [ source 20 target 21 label "=" ]
		edge [ source 20 target 22 label "-" ]
		edge [ source 20 target 23 label "-" ]
	]
	right [
		edge [ source 1 target 2 label "-" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 7 target 8 label "=" ]
		edge [ source 20 target 4 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 4
		op "="
		count 1
		nodeLabels [ label "N" label "N+" ]
		edgeLabels [ label "#" label "-" ]
	]
]