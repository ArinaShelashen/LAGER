rule [
	labelType "term"
	left [
		edge [ source 5 target 6 label "-" ]
		edge [ source 8 target 9 label "-" ]
	]
	context [
		node [ id 5 label "O" ]
		node [ id 6 label "H" ]
		node [ id 7 label "C" ]
		node [ id 8 label "_X" ]
		node [ id 9 label "Cl" ]
		node [ id 10 label "O" ]
		edge [ source 5 target 7 label "-" ]
		edge [ source 8 target 10 label "=" ]
	]
	right [
		edge [ source 9 target 6 label "-" ]
		edge [ source 8 target 5 label "-" ]
	]
	constrainAdj [
		id 7
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainLabelAny [ label "_X" labels [ label "C" label "S" ] ]
]