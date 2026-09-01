rule [
	labelType "term"
	left [
		edge [ source 2 target 1 label "=" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 6 target 7 label "-" ]
		edge [ source 1 target 3 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "O" ]
		node [ id 4 label "H" ]
		node [ id 5 label "H" ]
		node [ id 6 label "H" ]
		node [ id 7 label "H" ]
		node [ id 9 label "_X" ]
		edge [ source 9 target 1 label "-" ]
	]
	right [
		edge [ source 4 target 2 label "-" ]
		edge [ source 6 target 1 label "-" ]
		edge [ source 7 target 1 label "-" ]
		edge [ source 2 target 1 label "-" ]
		edge [ source 5 target 3 label "-" ]
	]
	constrainLabelAny [ label "_X" labels [ label "C" label "H" ] ]
]