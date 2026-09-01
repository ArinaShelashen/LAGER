rule [
	labelType "term"
	left [
		edge [ source 6 target 7 label "=" ]
		edge [ source 2 target 4 label "-" ]
		edge [ source 9 target 10 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 3 label "_X" ]
		node [ id 4 label "H" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 9 label "H" ]
		node [ id 10 label "H" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 2 target 3 label "-" ]
	]
	right [
		edge [ source 2 target 6 label "-" ]
		edge [ source 10 target 7 label "-" ]
		edge [ source 9 target 7 label "-" ]
		edge [ source 4 target 6 label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 2
		nodeLabels [ label "C" label "H" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 3
		op "="
		count 0
		nodeLabels [ label "O" ]
	]

	constrainLabelAny [ label "_X" labels [ label "H" label "C" ] ]
]