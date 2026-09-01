rule [
	labelType "term"
	left [
		edge [ source 2 target 5 label "-" ]
		edge [ source 12 target 1 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "_X" ]
		node [ id 5 label "H" ]
		node [ id 12 label "_X" ]
	]
	right [
		edge [ source 12 target 2 label "-" ]
		edge [ source 1 target 5 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainLabelAny [ label "_X" labels [ label "Cl" label "Br" ] ]
]