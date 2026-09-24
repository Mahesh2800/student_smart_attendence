import { useEffect, useState } from 'react'
import api from '../../api/axiosConfig'
import { CrudPage } from './ManageDepartments'
export default function ManageFaculty() { const [items, setItems] = useState([]); useEffect(() => { api.get('/attendance/faculty/').then(({ data }) => setItems(data.results || data)).catch(() => {}) }, []); return <CrudPage title="Faculty" kicker="PEOPLE" description="See teaching ownership and department coverage." headers={['Employee ID', 'Name', 'Designation', 'Department']} rows={items.map((item) => [item.employee_id, item.name || item.username, item.designation, item.department])} /> }
