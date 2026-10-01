async function runQuery(){

const query = document.getElementById("query").value

const results = document.getElementById("results")
results.innerText = "Running query..."

try {

const res = await fetch("/query",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({query})

})

const data = await res.json()

if(data.error){

results.innerText=data.error
return

}

results.innerHTML = ""

const table = document.createElement("table")
const headerRow = document.createElement("tr")

for(const c of data.columns){

const th = document.createElement("th")
th.textContent = c
headerRow.appendChild(th)

}

table.appendChild(headerRow)

for(const row of data.rows){

const tr = document.createElement("tr")

for(const cell of row){

const td = document.createElement("td")
td.textContent = cell === null ? "null" : String(cell)
tr.appendChild(td)

}

table.appendChild(tr)

}

results.appendChild(table)

} catch (err) {

results.innerText = "Query failed: " + err.message

}

}

document.getElementById("query").addEventListener("keydown", function(event){

if((event.ctrlKey || event.metaKey) && event.key === "Enter"){

event.preventDefault()
runQuery()

}

})
