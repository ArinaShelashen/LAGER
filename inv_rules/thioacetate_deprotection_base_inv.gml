rule [
	left [
		edge [ source 2 target 6 label "-" ]
		edge [ source 1 target 7 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
		node [ id 3 label "C" ]
		node [ id 4 label "O" ]
		node [ id 5 label "C" ]
		node [ id 1 label "S" ]
		node [ id 6 label "O-" ]
		node [ id 7 label "H" ]
		edge [ source 2 target 4 label "=" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 5 target 1 label "-" ]
	]
	right [
		edge [ source 7 target 6 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
]