rule [
	labelType "term"
	left [
		node [ id 2 label "Cl-" ]
		node [ id 3 label "I" ]
		edge [ source 1 target 3 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
	]
	right [
		node [ id 2 label "Cl" ]
		node [ id 3 label "I-" ]
		edge [ source 1 target 2 label "-" ]
	]
]