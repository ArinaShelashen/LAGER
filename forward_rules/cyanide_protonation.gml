rule [
	left [
		node [ id 1 label "C-" ]
		node [ id 4 label "O" ]
		edge [ source 3 target 4 label "-" ]
	]
	context [
		node [ id 2 label "N" ]
		node [ id 3 label "H" ]
		node [ id 5 label "C" ]
		node [ id 6 label "O" ]
		edge [ source 2 target 1 label "#" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 5 target 6 label "=" ]
	]
	right [
		node [ id 1 label "C" ]
		node [ id 4 label "O-" ]
		edge [ source 3 target 1 label "-" ]
	]
]