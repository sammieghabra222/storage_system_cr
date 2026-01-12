'use client';

import { useAuthStore } from '@/stores/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function SettingsPage() {
  const { user, tenant } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuracion</h1>
        <p className="text-gray-600">Administre la configuracion de su cuenta y negocio</p>
      </div>

      {/* Business Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion del Negocio</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nombre del Negocio"
              defaultValue={tenant?.name}
            />
            <Input
              label="Nombre Legal"
              defaultValue={tenant?.legal_name || ''}
              placeholder="Razon social"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Cedula Juridica"
              defaultValue={tenant?.cedula_juridica || ''}
              placeholder="3-101-123456"
            />
            <Input
              label="Correo del Negocio"
              type="email"
              defaultValue={tenant?.email}
            />
          </div>
          <Input
            label="Telefono"
            defaultValue={tenant?.phone || ''}
            placeholder="2222-2222"
          />
          <Input
            label="Direccion"
            defaultValue={tenant?.address || ''}
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Ciudad"
              defaultValue={tenant?.city || ''}
            />
            <Input
              label="Provincia"
              defaultValue={tenant?.province || ''}
            />
            <Input
              label="Codigo Postal"
              defaultValue={tenant?.postal_code || ''}
            />
          </div>
          <Button>Guardar Cambios</Button>
        </CardContent>
      </Card>

      {/* Payment Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Configuracion de Pagos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Numero SINPE Movil"
            defaultValue={tenant?.sinpe_number || ''}
            placeholder="8888-8888"
            helperText="Este numero se mostrara a los clientes para que envien pagos"
          />
          <Button>Guardar Numero SINPE</Button>
        </CardContent>
      </Card>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Perfil Personal</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nombre"
              defaultValue={user?.first_name}
            />
            <Input
              label="Apellido"
              defaultValue={user?.last_name}
            />
          </div>
          <Input
            label="Correo Electronico"
            type="email"
            defaultValue={user?.email}
          />
          <div className="pt-4 border-t">
            <h4 className="font-medium text-gray-900 mb-4">Cambiar Contrasena</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Contrasena Actual"
                type="password"
              />
              <div></div>
              <Input
                label="Nueva Contrasena"
                type="password"
              />
              <Input
                label="Confirmar Contrasena"
                type="password"
              />
            </div>
          </div>
          <Button>Guardar Perfil</Button>
        </CardContent>
      </Card>
    </div>
  );
}
