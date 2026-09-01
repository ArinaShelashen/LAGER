rule [
	labelType "term"
	left [
		edge [ source 7 target 8 label "-" ]
		edge [ source 10 target 9 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "S" ]
		node [ id 3 label "H" ]
		node [ id 4 label "C" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "Si" ]
		node [ id 8 label "N" ]
		node [ id 9 label "H" ]
		node [ id 10 label "O" ]
		node [ id 11 label "_X" ]
		node [ id 12 label "C" ]
		node [ id 13 label "O" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 4 target 7 label "-" ]
		edge [ source 5 target 7 label "-" ]
		edge [ source 6 target 7 label "-" ]
		edge [ source 11 target 10 label "-" ]
		edge [ source 12 target 13 label "=" ]
		edge [ source 2 target 12 label "-" ]
		edge [ source 3 target 8 label "-" ]
		edge [ source 8 target 12 label "-" ]
	]
	right [
		edge [ source 10 target 7 label "-" ]
		edge [ source 9 target 8 label "-" ]
	]
	constrainAdj [
		id 11
		op "="
		count 0
		nodeLabels [  ]
		edgeLabels [ label "=" ]
	]
	constrainLabelAny [ label "_X" labels [ label "C" label "H" ] ]
]