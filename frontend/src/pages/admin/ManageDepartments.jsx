import { useEffect, useState } from 'react'
import api from '../../api/axiosConfig'
export default function ManageDepartments() {
	const [items, setItems] = useState([])
	const [showForm, setShowForm] = useState(false)
	const [form, setForm] = useState({ name: '', code: '' })
	const [error, setError] = useState('')
	const [search, setSearch] = useState('')
	const load = () => api.get('/attendance/departments/').then(({ data }) => setItems(data.results || data)).catch(() => setError('Unable to load departments.'))
	useEffect(() => { load() }, [])
	const submit = async (event) => {
		event.preventDefault()
		setError('')
		try { await api.post('/attendance/departments/', { name: form.name.trim(), code: form.code.trim().toUpperCase() }); setForm({ name: '', code: '' }); setShowForm(false); load() } catch (requestError) { setError(requestError.response?.data?.detail || 'Department code or name may already exist.') }
	}
	const filteredItems = items.filter((item) => `${item.code} ${item.name}`.toLowerCase().includes(search.toLowerCase()))
	return <><div className="page-heading"><div><span className="eyebrow">STRUCTURE</span><h1>Departments</h1><p>Organise academic ownership across the college.</p></div><button className="button primary" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close form' : '+ Add department'}</button></div>{showForm && <form className="panel inline-form" onSubmit={submit}><label>Department name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="e.g. Computer Science" /></label><label>Department code<input required maxLength="20" value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} placeholder="e.g. CSE" /></label><button className="button primary">Create department</button>{error && <span className="form-error">{error}</span>}</form>}<div className="panel table-panel"><div className="toolbar"><input placeholder="Search departments" value={search} onChange={(event) => setSearch(event.target.value)} /><span className="muted">{filteredItems.length} records</span></div><div className="table-wrap"><table><thead><tr><th>Code</th><th>Department</th></tr></thead><tbody>{filteredItems.length ? filteredItems.map((item) => <tr key={item.id}><td>{item.code}</td><td>{item.name}</td></tr>) : <tr><td colSpan="2">No departments match your search.</td></tr>}</tbody></table></div></div></>
}
function CrudPage({ title, kicker, description, headers, rows }) { const [search, setSearch] = useState(''); const filteredRows = rows.filter((row) => row.join(' ').toLowerCase().includes(search.toLowerCase())); return <><div className="page-heading"><div><span className="eyebrow">{kicker}</span><h1>{title}</h1><p>{description}</p></div></div><div className="panel table-panel"><div className="toolbar"><input placeholder={`Search ${title.toLowerCase()}`} value={search} onChange={(event) => setSearch(event.target.value)} /><span className="muted">{filteredRows.length} records</span></div><div className="table-wrap"><table><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{filteredRows.length ? filteredRows.map((row, index) => <tr key={index}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>) : <tr><td colSpan={headers.length}>No records match your search.</td></tr>}</tbody></table></div></div></> }
export { CrudPage }
